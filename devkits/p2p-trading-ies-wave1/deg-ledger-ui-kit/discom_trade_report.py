#!/usr/bin/env python3
"""
DISCOM Trade Report — WhatsApp-friendly summary of trades per DISCOM.

Queries the DEG Ledger for trades involving configured DISCOMs whose
delivery start time falls within the last 30 to last 2 days (midnight IST
boundaries) and reports trade counts, allocation status, and pending
trades by delivery day.

Usage:
    python3 discom_trade_report.py
    python3 discom_trade_report.py --csv trades.csv

Credentials and LEDGER_URL are read from .env (same as server.py).
"""

import argparse
import base64
import csv
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ── Load .env ──
DIR = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(DIR, ".env")
if os.path.isfile(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())

# ── Config ──
SUBSCRIBER_ID = os.environ.get("SUBSCRIBER_ID")
RECORD_ID = os.environ.get("RECORD_ID")
SIGNING_PRIVATE_KEY = os.environ.get("SIGNING_PRIVATE_KEY")
LEDGER_URL = os.environ.get("LEDGER_URL")
EXPIRY_SECONDS = 300
PAGE_SIZE = 500

# ── Valid DISCOMs to track ──
VALID_DISCOMS = ["PVVNL", "TPDDL", "BRPL"]

# ── IST timezone (UTC+05:30) ──
IST = timezone(timedelta(hours=5, minutes=30))


def _load_private_key():
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(SIGNING_PRIVATE_KEY))


def _sign_payload(body: bytes, private_key) -> str:
    digest = hashlib.blake2b(body, digest_size=64).digest()
    digest_b64 = base64.b64encode(digest).decode()
    created = int(time.time())
    expires = created + EXPIRY_SECONDS
    signing_string = (
        f"(created): {created}\n"
        f"(expires): {expires}\n"
        f"digest: BLAKE-512={digest_b64}"
    )
    signature = private_key.sign(signing_string.encode())
    sig_b64 = base64.b64encode(signature).decode()
    return (
        f'Signature keyId="{SUBSCRIBER_ID}|{RECORD_ID}|ed25519"'
        f',algorithm="ed25519"'
        f',created="{created}"'
        f',expires="{expires}"'
        f',headers="(created) (expires) digest"'
        f',signature="{sig_b64}"'
    )


def _fetch_all_trades(api_url, private_key, from_iso, to_iso):
    """Paginate through all trades in the given date range."""
    all_records = []
    offset = 0
    while True:
        payload = {
            "deliveryStartFrom": from_iso,
            "deliveryStartTo": to_iso,
            "sort": "deliveryStartTime",
            "sortOrder": "asc",
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        body = json.dumps(payload, separators=(",", ":")).encode()
        auth = _sign_payload(body, private_key)
        req = urllib.request.Request(
            api_url, data=body,
            headers={"Content-Type": "application/json", "Authorization": auth},
            method="POST",
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx) as resp:
            result = json.loads(resp.read())
        records = result.get("records", [])
        all_records.extend(records)
        print(f"  Fetched {len(records)} (offset={offset}, total={len(all_records)})", file=sys.stderr)
        if len(records) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return all_records


def _delivery_date_key(trade):
    """Extract delivery date as (sortable_str, display_str) from a trade record."""
    raw = trade.get("deliveryStartTime") or trade.get("tradeTime") or ""
    if not raw:
        return ("9999-99-99", "Unknown")
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        ist_dt = dt.astimezone(IST)
        return (ist_dt.strftime("%Y-%m-%d"), ist_dt.strftime("%d %b"))
    except (ValueError, TypeError):
        return ("9999-99-99", "Unknown")


def _fmt_ist(raw):
    """Convert an ISO timestamp string to a human-readable IST string."""
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return raw


def _get_energy(trade):
    details = trade.get("tradeDetails") or []
    return sum(d.get("tradeQty", 0) for d in details if d.get("tradeUnit") == "KWH")


def _get_trade_type(trade):
    details = trade.get("tradeDetails") or []
    return ", ".join(d["tradeType"] for d in details if d.get("tradeType"))


def _get_delivery_start(trade):
    details = trade.get("tradeDetails") or []
    if details:
        for key in ("deliveryStartTime", "deliveryStart"):
            v = details[0].get(key)
            if v:
                return v
    for key in ("deliveryStartTime", "deliveryStart"):
        v = trade.get(key)
        if v:
            return v
    return ""


def _get_delivery_end(trade):
    details = trade.get("tradeDetails") or []
    if details:
        for key in ("deliveryEndTime", "deliveryEnd"):
            v = details[0].get(key)
            if v:
                return v
    for key in ("deliveryEndTime", "deliveryEnd"):
        v = trade.get(key)
        if v:
            return v
    return ""


def _duration_hours(start_raw, end_raw):
    if not start_raw or not end_raw:
        return ""
    try:
        start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
        hours = (end - start).total_seconds() / 3600
        return f"{hours:.2f}"
    except (ValueError, TypeError):
        return ""


CSV_COLUMNS = [
    "Trade Time (IST)",
    "Delivery Start (IST)",
    "Duration (h)",
    "Qty (KWH)",
    "Buyer Alloc",
    "Seller Alloc",
    "Buyer Status",
    "Seller Status",
    "Buyer Discom",
    "Seller Discom",
    "Buyer ID",
    "Seller ID",
    "Buyer App",
    "Seller App",
    "Trade Type",
    "Transaction ID",
    "Record ID",
]


def write_csv(trades, path):
    """Write all trades to a CSV file with the same columns as the UI table."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in trades:
            start_raw = _get_delivery_start(r)
            end_raw = _get_delivery_end(r)
            writer.writerow({
                "Trade Time (IST)": _fmt_ist(r.get("tradeTime", "")),
                "Delivery Start (IST)": _fmt_ist(start_raw),
                "Duration (h)": _duration_hours(start_raw, end_raw),
                "Qty (KWH)": f"{_get_energy(r):.2f}",
                "Buyer Alloc": r.get("buyerDiscomAllocation", ""),
                "Seller Alloc": r.get("sellerDiscomAllocation", ""),
                "Buyer Status": r.get("statusBuyerDiscom", ""),
                "Seller Status": r.get("statusSellerDiscom", ""),
                "Buyer Discom": r.get("discomIdBuyer", ""),
                "Seller Discom": r.get("discomIdSeller", ""),
                "Buyer ID": r.get("buyerId", ""),
                "Seller ID": r.get("sellerId", ""),
                "Buyer App": r.get("platformIdBuyer", ""),
                "Seller App": r.get("platformIdSeller", ""),
                "Trade Type": _get_trade_type(r),
                "Transaction ID": r.get("transactionId", ""),
                "Record ID": r.get("recordId", ""),
            })
    print(f"CSV written: {path} ({len(trades)} rows)", file=sys.stderr)


def generate_report(csv_path=None):
    """Fetch trades from ledger and print a WhatsApp-friendly DISCOM trade report."""
    if not LEDGER_URL:
        print("Error: LEDGER_URL not set in .env or environment", file=sys.stderr)
        sys.exit(1)

    api_url = f"{LEDGER_URL.rstrip('/')}/ledger/get"
    private_key = _load_private_key()

    # Date range: fetch covers both the historical report window (T-30 to T-2)
    # and the near-term trend window (T-1 to T+1), all at midnight IST.
    now_ist = datetime.now(IST)
    today_midnight = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = today_midnight - timedelta(days=30)
    window_end = today_midnight - timedelta(days=2)  # exclusive
    trend_end = today_midnight + timedelta(days=2)   # exclusive; includes all of tomorrow

    start_utc = window_start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_utc = trend_end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"Fetching trades {window_start.strftime('%d %b')} – {trend_end.strftime('%d %b %Y')} IST ...", file=sys.stderr)
    all_trades = _fetch_all_trades(api_url, private_key, start_utc, end_utc)

    # Per-discom stats: total, allocated, unallocated, unallocated by delivery day
    stats = {d: {"total": 0, "allocated": 0, "unallocated": 0,
                 "unalloc_days": defaultdict(int)} for d in VALID_DISCOMS}

    # Near-term delivery trend (unique trades involving a valid DISCOM)
    yesterday_key = (today_midnight - timedelta(days=1)).strftime("%Y-%m-%d")
    today_key = today_midnight.strftime("%Y-%m-%d")
    tomorrow_key = (today_midnight + timedelta(days=1)).strftime("%Y-%m-%d")
    trend = {yesterday_key: 0, today_key: 0, tomorrow_key: 0}

    window_start_key = window_start.strftime("%Y-%m-%d")
    window_end_key = window_end.strftime("%Y-%m-%d")

    for trade in all_trades:
        buyer_discom = trade.get("discomIdBuyer", "")
        seller_discom = trade.get("discomIdSeller", "")
        if buyer_discom.startswith("TEST") or seller_discom.startswith("TEST"):
            continue
        sort_key, display_day = _delivery_date_key(trade)

        # Trend: count each trade once if it touches a tracked DISCOM
        if sort_key in trend and (buyer_discom in stats or seller_discom in stats):
            trend[sort_key] += 1

        # Existing per-DISCOM stats are limited to the historical window
        if not (window_start_key <= sort_key < window_end_key):
            continue

        # Buyer side
        if buyer_discom in stats:
            stats[buyer_discom]["total"] += 1
            status = (trade.get("statusBuyerDiscom") or "").upper()
            if status == "COMPLETED":
                stats[buyer_discom]["allocated"] += 1
            else:
                stats[buyer_discom]["unallocated"] += 1
                stats[buyer_discom]["unalloc_days"][(sort_key, display_day)] += 1

        # Seller side
        if seller_discom in stats:
            stats[seller_discom]["total"] += 1
            status = (trade.get("statusSellerDiscom") or "").upper()
            if status == "COMPLETED":
                stats[seller_discom]["allocated"] += 1
            else:
                stats[seller_discom]["unallocated"] += 1
                stats[seller_discom]["unalloc_days"][(sort_key, display_day)] += 1

    # ── Build WhatsApp-friendly report ──
    today_str = now_ist.strftime("%d %b %Y")
    window_str = f"{window_start.strftime('%d %b')} – {window_end.strftime('%d %b %Y')}"

    lines = [
        f"*IES P2P Trade Report*",
        f"Date: {today_str}",
        f"*Delivery trend:* Yesterday {trend[yesterday_key]} · Today {trend[today_key]} · Tomorrow {trend[tomorrow_key]}",
        f"Delivery window: {window_str}",
        f"Trades delivered in this window:",
        "",
    ]

    for d in VALID_DISCOMS:
        s = stats[d]
        lines.append(f"*{d}:* {s['total']} trades ({s['allocated']} allocated, {s['unallocated']} pending)")

    tot = sum(s["total"] for s in stats.values())
    alloc = sum(s["allocated"] for s in stats.values())
    unalloc = sum(s["unallocated"] for s in stats.values())
    lines.append("")
    lines.append(f"*Total:* {tot} ({alloc} allocated, {unalloc} pending)")

    # Unallocated breakdown by day
    has_pending = any(s["unallocated"] > 0 for s in stats.values())
    if has_pending:
        lines.append("")
        lines.append("*Pending allocation by delivery day:*")
        for d in VALID_DISCOMS:
            s = stats[d]
            if s["unallocated"] == 0:
                continue
            day_parts = [f"{disp}: {cnt}" for (_, disp), cnt
                         in sorted(s["unalloc_days"].items())]
            lines.append(f"{d} — " + ", ".join(day_parts))

    report = "\n".join(lines)
    print(report)

    if csv_path:
        write_csv(all_trades, csv_path)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DISCOM Trade Report")
    parser.add_argument("--csv", metavar="FILE", help="Optional path to write all trades as a CSV file")
    args = parser.parse_args()
    generate_report(csv_path=args.csv)
