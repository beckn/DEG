#!/usr/bin/env python3
"""
DISCOM Trade Report — WhatsApp-friendly summary of trades per DISCOM.

Two modes:

  Daily (default) — trades whose delivery start falls within the last 30 to
  last 2 days (midnight IST boundaries), reported as counts, allocation
  status, and pending trades by delivery day.

  Range (--from/--to) — an arbitrary delivery window, reported as aligned
  monospace tables: totals, per-DISCOM buy/sell/pending, per-platform
  buy/sell/pending, and pending by month.

Usage:
    python3 discom_trade_report.py
    python3 discom_trade_report.py --csv trades.csv
    python3 discom_trade_report.py --fetch-days 300 --csv trades.csv

    python3 discom_trade_report.py --from 2026-01-01 --to 2026-08-31
    python3 discom_trade_report.py --from 2026-01-01 --to 2026-08-31 \
        --pending-detail --csv trades.csv
    python3 discom_trade_report.py --from 2026-04-01 --to 2026-06-30 \
        --discoms BRPL,TPDDL --no-mono

Both --from and --to are inclusive calendar dates in IST.

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

# ── Valid DISCOMs to track (override per run with --discoms) ──
VALID_DISCOMS = ["PVVNL", "TPDDL", "BRPL"]

# ── Number of top buyer/seller platforms to highlight ──
TOP_PLATFORMS_N = 3

# ── How far back the daily report fetches (override with --fetch-days) ──
DEFAULT_FETCH_DAYS = 30

# Display name per subscriber ID for the range-report platform tables.
# Subscriber IDs sharing a name are summed into a single row, which is how a
# platform running several subscribers (BAP/BPP pairs, staging and production,
# rebranded hostnames) is reported as one platform.
#
# A subscriber ID that is not listed here is NOT dropped or shortened — it is
# reported verbatim under its own row, so a newly onboarded platform shows up
# as itself. Add it here once you know which platform it belongs to.
PLATFORM_LABELS = {
    "pulseenergy_interstate_p2p_test_bap.com": "PulseEnergy",
    "pulseenergy_interstate_p2p_test_bpp.com": "PulseEnergy",
    "p2p-ies-bap-pulseenergy.io": "PulseEnergy",
    "p2p-ies-bpp-pulseenergy.io": "PulseEnergy",
    "bap.p2p.ies.kazam.energy": "Kazam",
    "bpp.p2p.ies.kazam.energy": "Kazam",
    "dev-deg-bap.powerxchange.io": "PowerXchange",
    "dev-deg-bpp.powerxchange.io": "PowerXchange",
    "p2p.terrarexenergy.com": "TerrareX",
    "bap.charzpe.com": "Charzpe",
    "bpp.charzpe.com": "Charzpe",
    "clickpower.in": "ClickPower",
    "iris-cms.com": "Iris",
}

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


def _platform_label(platform):
    """Display name for a subscriber ID, or the ID verbatim if it has no alias."""
    return PLATFORM_LABELS.get(platform, platform)


def _is_test_trade(trade):
    """True if either side carries a TEST_* DISCOM placeholder."""
    return (trade.get("discomIdBuyer") or "").startswith("TEST") or \
           (trade.get("discomIdSeller") or "").startswith("TEST")


def _side_pending(trade, discoms, buyer_side):
    """True if this side's DISCOM is tracked and its allocation is not COMPLETED."""
    discom_key = "discomIdBuyer" if buyer_side else "discomIdSeller"
    status_key = "statusBuyerDiscom" if buyer_side else "statusSellerDiscom"
    if trade.get(discom_key) not in discoms:
        return False
    return (trade.get(status_key) or "").upper() != "COMPLETED"


def select_valid_trades(all_trades, discoms, start_key, end_key):
    """Non-TEST trades touching a tracked DISCOM, delivered within [start, end]."""
    valid = []
    for trade in all_trades:
        if _is_test_trade(trade):
            continue
        if trade.get("discomIdBuyer") not in discoms and \
           trade.get("discomIdSeller") not in discoms:
            continue
        sort_key, _ = _delivery_date_key(trade)
        if not (start_key <= sort_key <= end_key):
            continue
        valid.append(trade)
    return valid


def build_range_report(all_trades, start, end, discoms=None,
                       pending_detail=False, monthly=False, mono=True):
    """Build an aligned monospace trade report for an arbitrary delivery window.

    Each trade is counted once per side whose DISCOM is tracked, so the buy and
    sell columns sum above the unique trade total whenever both counterparties
    are tracked DISCOMs.
    """
    discoms = list(discoms or VALID_DISCOMS)
    start_key = start.strftime("%Y-%m-%d")
    end_key = end.strftime("%Y-%m-%d")
    valid = select_valid_trades(all_trades, discoms, start_key, end_key)

    discom_stats = {d: {"buy": 0, "sell": 0, "kwh": 0.0, "pend": 0} for d in discoms}
    buyer_platforms = defaultdict(lambda: {"trades": 0, "kwh": 0.0, "pend": 0})
    seller_platforms = defaultdict(lambda: {"trades": 0, "kwh": 0.0, "pend": 0})
    month_totals = defaultdict(lambda: {"trades": 0, "kwh": 0.0})
    pending_months = defaultdict(int)
    pending_cross = defaultdict(int)

    total_kwh = 0.0
    pending_trades = 0
    pending_kwh = 0.0

    for trade in valid:
        energy = _get_energy(trade)
        total_kwh += energy
        month = _delivery_date_key(trade)[0][:7]
        month_totals[month]["trades"] += 1
        month_totals[month]["kwh"] += energy

        buy_pending = _side_pending(trade, discoms, buyer_side=True)
        sell_pending = _side_pending(trade, discoms, buyer_side=False)
        if buy_pending or sell_pending:
            pending_trades += 1
            pending_kwh += energy
            pending_months[month] += 1

        buyer_discom = trade.get("discomIdBuyer")
        if buyer_discom in discom_stats:
            discom_stats[buyer_discom]["buy"] += 1
            discom_stats[buyer_discom]["kwh"] += energy
            discom_stats[buyer_discom]["pend"] += buy_pending

        seller_discom = trade.get("discomIdSeller")
        if seller_discom in discom_stats:
            discom_stats[seller_discom]["sell"] += 1
            discom_stats[seller_discom]["kwh"] += energy
            discom_stats[seller_discom]["pend"] += sell_pending

        # Keyed by display name, so a platform trading under several
        # subscriber IDs is summed into a single row.
        buyer_app = trade.get("platformIdBuyer")
        if buyer_app:
            label = _platform_label(buyer_app)
            buyer_platforms[label]["trades"] += 1
            buyer_platforms[label]["kwh"] += energy
            buyer_platforms[label]["pend"] += buy_pending

        seller_app = trade.get("platformIdSeller")
        if seller_app:
            label = _platform_label(seller_app)
            seller_platforms[label]["trades"] += 1
            seller_platforms[label]["kwh"] += energy
            seller_platforms[label]["pend"] += sell_pending

        if sell_pending and seller_app:
            pending_cross[("sell", seller_discom, _platform_label(seller_app))] += 1
        if buy_pending and buyer_app:
            pending_cross[("buy", buyer_discom, _platform_label(buyer_app))] += 1

    lines = ["IES P2P TRADE REPORT",
             f"Delivery: {start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}"]

    if valid:
        first = min(_delivery_date_key(t)[0] for t in valid)
        last = max(_delivery_date_key(t)[0] for t in valid)
        if first != start_key or last != end_key:
            lines.append(f"(first trade {_short_day(first)}, last {_short_day(last)})")
    lines.append("")

    lines.append(f"TOTAL VALID TRADES : {len(valid)}")
    lines.append(f"TOTAL ENERGY       : {total_kwh:.0f} kWh")
    lines.append(f"PENDING TRADES     : {pending_trades} ({pending_kwh:.0f} kWh)")

    lines.append("")
    lines.append("BY DISCOM")
    lines.append(f"{'DISCOM':<8}{'Buy':>5}{'Sell':>7}{'kWh':>7}{'Pend':>6}")
    for d in discoms:
        s = discom_stats[d]
        lines.append(f"{d:<8}{s['buy']:>5}{s['sell']:>7}{s['kwh']:>7.0f}{s['pend']:>6}")

    def _platform_table(title, stats):
        if not stats:
            return
        # Widen to the longest name present, so an un-aliased subscriber ID
        # prints in full without knocking the columns out of alignment.
        width = max([len("Platform")] + [len(name) for name in stats])
        lines.append("")
        lines.append(title)
        lines.append(f"{'Platform':<{width}}{'Trades':>7}{'kWh':>6}{'Pend':>6}")
        ordered = sorted(stats.items(),
                         key=lambda kv: (kv[1]["trades"], kv[1]["kwh"]), reverse=True)
        for name, ps in ordered:
            lines.append(f"{name:<{width}}"
                         f"{ps['trades']:>7}{ps['kwh']:>6.0f}{ps['pend']:>6}")

    _platform_table("SELLER PLATFORMS", seller_platforms)
    _platform_table("BUYER PLATFORMS", buyer_platforms)

    if monthly:
        lines.append("")
        lines.append("BY MONTH")
        lines.append(f"{'Month':<10}{'Trades':>7}{'kWh':>7}")
        for month in sorted(month_totals):
            m = month_totals[month]
            lines.append(f"{_short_month(month):<10}{m['trades']:>7}{m['kwh']:>7.0f}")

    if pending_months:
        lines.append("")
        lines.append("PENDING BY MONTH")
        for month in sorted(pending_months):
            lines.append(f"{_short_month(month):<10}{pending_months[month]:>4}")

    if pending_detail and pending_cross:
        lines.append("")
        lines.append("PENDING DETAIL (discom x platform)")
        ordered = sorted(pending_cross.items(), key=lambda kv: -kv[1])
        width = max(len(name) for _, _, name in pending_cross)
        for (side, discom, name), count in ordered:
            tag = "sells" if side == "sell" else "buys "
            lines.append(f"{discom:<7}{tag} {name:<{width}}{count:>4}")

    lines.append("")
    lines.append("Note: DISCOM/platform rows count each")
    lines.append("trade once per side, so columns sum")
    lines.append(f"above {len(valid)}.")

    report = "\n".join(lines)
    if mono:
        report = f"```\n{report}\n```"
    return report


def _short_day(sort_key):
    """'2026-02-18' -> '18 Feb'."""
    try:
        return datetime.strptime(sort_key, "%Y-%m-%d").strftime("%d %b")
    except ValueError:
        return sort_key


def _short_month(month_key):
    """'2026-02' -> 'Feb 2026'."""
    try:
        return datetime.strptime(month_key, "%Y-%m").strftime("%b %Y")
    except ValueError:
        return month_key


def _fetch_window(start, end_exclusive):
    """Fetch every trade delivered in [start, end_exclusive) IST."""
    if not LEDGER_URL:
        print("Error: LEDGER_URL not set in .env or environment", file=sys.stderr)
        sys.exit(1)

    api_url = f"{LEDGER_URL.rstrip('/')}/ledger/get"
    private_key = _load_private_key()
    start_utc = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_utc = end_exclusive.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    print(f"Fetching trades {start.strftime('%d %b %Y')} – "
          f"{end_exclusive.strftime('%d %b %Y')} IST ...", file=sys.stderr)
    return _fetch_all_trades(api_url, private_key, start_utc, end_utc)


def generate_report(csv_path=None, fetch_days=DEFAULT_FETCH_DAYS):
    """Fetch trades from ledger and print a WhatsApp-friendly DISCOM trade report."""
    # Date range: fetch covers both the historical report window (T-30 to T-2)
    # and the near-term trend window (T-1 to T+1), all at midnight IST.
    now_ist = datetime.now(IST)
    today_midnight = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = today_midnight - timedelta(days=fetch_days)
    trend_end = today_midnight + timedelta(days=2)   # exclusive; includes all of tomorrow

    all_trades = _fetch_window(window_start, trend_end)

    report = build_report(all_trades, now_ist)
    print(report)

    if csv_path:
        write_csv(all_trades, csv_path)

    return report


def generate_range_report(start, end, csv_path=None, discoms=None,
                          pending_detail=False, monthly=False, mono=True):
    """Fetch and print a report for an arbitrary inclusive IST delivery window."""
    all_trades = _fetch_window(start, end + timedelta(days=1))

    report = build_range_report(all_trades, start, end, discoms=discoms,
                                pending_detail=pending_detail,
                                monthly=monthly, mono=mono)
    print(report)

    if csv_path:
        write_csv(all_trades, csv_path)

    return report


def build_report(all_trades, now_ist):
    """Build the WhatsApp-friendly DISCOM trade report string from fetched trades."""
    today_midnight = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = today_midnight - timedelta(days=30)
    window_end = today_midnight - timedelta(days=2)  # exclusive

    # Per-discom stats: total, allocated, unallocated, unallocated by delivery day
    stats = {d: {"total": 0, "allocated": 0, "unallocated": 0,
                 "unalloc_days": defaultdict(int)} for d in VALID_DISCOMS}

    # Buyer/seller platform activity over the historical window (trades + energy)
    buyer_platform_stats = defaultdict(lambda: {"trades": 0, "energy": 0.0})
    seller_platform_stats = defaultdict(lambda: {"trades": 0, "energy": 0.0})

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

        # Buyer/seller platform activity, for trades touching a tracked DISCOM.
        # Each trade counts once for its buyer app and once for its seller app.
        if buyer_discom in stats or seller_discom in stats:
            energy = _get_energy(trade)
            buyer_app = trade.get("platformIdBuyer")
            seller_app = trade.get("platformIdSeller")
            if buyer_app:
                buyer_platform_stats[buyer_app]["trades"] += 1
                buyer_platform_stats[buyer_app]["energy"] += energy
            if seller_app:
                seller_platform_stats[seller_app]["trades"] += 1
                seller_platform_stats[seller_app]["energy"] += energy

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

    # Top buyer/seller platforms by trade count over the delivery window
    def _append_top_platforms(label, platform_stats):
        if not platform_stats:
            return
        top = sorted(
            platform_stats.items(),
            key=lambda kv: (kv[1]["trades"], kv[1]["energy"]),
            reverse=True,
        )[:TOP_PLATFORMS_N]
        lines.append("")
        lines.append(f"*Top {len(top)} {label} ({window_str}):*")
        for i, (platform, ps) in enumerate(top, 1):
            lines.append(f"{i}. {platform} — {ps['trades']} trades, {ps['energy']:.1f} KWH")

    _append_top_platforms("seller platforms", seller_platform_stats)
    _append_top_platforms("buyer platforms", buyer_platform_stats)

    report = "\n".join(lines)
    return report


def _parse_ist_date(value):
    try:
        naive = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {value!r}")
    return naive.replace(tzinfo=IST)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DISCOM Trade Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Without --from/--to, reports the default rolling window "
               "(delivery T-30 to T-2) as the daily WhatsApp summary.",
    )
    parser.add_argument("--csv", metavar="FILE",
                        help="Also write every fetched trade to this CSV file")
    parser.add_argument("--from", dest="date_from", metavar="YYYY-MM-DD",
                        type=_parse_ist_date,
                        help="Range mode: first delivery date, inclusive (IST)")
    parser.add_argument("--to", dest="date_to", metavar="YYYY-MM-DD",
                        type=_parse_ist_date,
                        help="Range mode: last delivery date, inclusive (IST)")
    parser.add_argument("--discoms", metavar="A,B,C",
                        help=f"Comma-separated DISCOMs to track "
                             f"(default: {','.join(VALID_DISCOMS)})")
    parser.add_argument("--fetch-days", type=int, default=DEFAULT_FETCH_DAYS,
                        metavar="N",
                        help=f"Daily mode: how many days back to fetch, useful "
                             f"for a wider --csv (default: {DEFAULT_FETCH_DAYS})")
    parser.add_argument("--monthly", action="store_true",
                        help="Range mode: add a trades-and-kWh-by-month table")
    parser.add_argument("--pending-detail", action="store_true",
                        help="Range mode: add a DISCOM x platform pending breakdown")
    parser.add_argument("--no-mono", dest="mono", action="store_false",
                        help="Range mode: omit the ``` fences used for WhatsApp")
    args = parser.parse_args()

    discoms = [d.strip() for d in args.discoms.split(",") if d.strip()] \
        if args.discoms else None

    if args.date_from or args.date_to:
        if not (args.date_from and args.date_to):
            parser.error("--from and --to must be given together")
        if args.date_to < args.date_from:
            parser.error("--to must not be earlier than --from")
        generate_range_report(args.date_from, args.date_to, csv_path=args.csv,
                              discoms=discoms, pending_detail=args.pending_detail,
                              monthly=args.monthly, mono=args.mono)
    else:
        if discoms:
            VALID_DISCOMS = discoms
        generate_report(csv_path=args.csv, fetch_days=args.fetch_days)
