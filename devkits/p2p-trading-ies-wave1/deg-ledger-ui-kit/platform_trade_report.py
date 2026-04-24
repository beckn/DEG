#!/usr/bin/env python3
"""
Platform Trade Report — counts trades per platform from the DEG Ledger.

For each trade, a platform can appear as platformIdBuyer and/or platformIdSeller.
This script counts total trades per platform (buyer + seller appearances combined)
and flags self-trades where the same platform is both buyer and seller.

Usage:
    python3 platform_trade_report.py --from-date 2026-03-01
    python3 platform_trade_report.py --from-date 2026-03-01 --to-date 2026-03-23
    python3 platform_trade_report.py --from-date 2026-03-01 --proxy  # use local proxy instead of direct API

Credentials are read from .env (same as server.py / generate_curls.py).
"""

import argparse
import base64
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

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
EXPIRY_SECONDS = 300
PAGE_SIZE = 500  # max allowed by API

# ── Platform ID → Display Name mapping ──
# Update this dict with your actual platform IDs once you see them in the output.
# Any platform ID not in this map will be displayed as-is.
PLATFORM_NAMES = {
    # "bap.ikiteq.example":       "Ikiteq / STEAM-A Labs",
    # "bap.pulse.example":        "Pulse energy",
    # "bap.atria.example":        "Atria University",
    # "bap.terrarex.example":     "Terra rex",
    # "bap.voltbrew.example":     "Voltbrew",
    # "bap.sundaygrid.example":   "Sundaygrid",
    # "bap.reconnect.example":    "Reconnect energy",
    # "bap.kazam.example":        "Kazam",
    # "bap.powerxchange.example": "Powerxchange",
}


def _load_private_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.from_private_bytes(base64.b64decode(SIGNING_PRIVATE_KEY))


def sign_payload(body: bytes, private_key) -> str:
    """Sign request body and return the Authorization header value."""
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


def fetch_page_direct(url: str, payload: dict, private_key) -> dict:
    """Call /ledger/get directly with signing."""
    body = json.dumps(payload, separators=(",", ":")).encode()
    auth = sign_payload(body, private_key)

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": auth,
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read())


def fetch_page_proxy(payload: dict) -> dict:
    """Call through the local proxy at localhost:8080 (no signing needed)."""
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        "http://localhost:8080/api/ledger/get",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_all_trades(from_date: str, to_date: str | None, use_proxy: bool,
                     ledger_url: str | None) -> list[dict]:
    """Paginate through all trades from from_date onwards."""
    private_key = None
    api_url = None

    if not use_proxy:
        if not ledger_url:
            print("Error: --ledger-url required when not using --proxy", file=sys.stderr)
            sys.exit(1)
        private_key = _load_private_key()
        api_url = f"{ledger_url.rstrip('/')}/ledger/get"

    all_records = []
    offset = 0

    while True:
        payload = {
            "tradeTimeFrom": from_date,
            "sort": "tradeTime",
            "sortOrder": "asc",
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        if to_date:
            payload["tradeTimeTo"] = to_date

        try:
            if use_proxy:
                result = fetch_page_proxy(payload)
            else:
                result = fetch_page_direct(api_url, payload, private_key)
        except Exception as e:
            print(f"Error fetching page at offset {offset}: {e}", file=sys.stderr)
            break

        records = result.get("records", [])
        total_count = result.get("count", len(records))

        all_records.extend(records)
        print(f"  Fetched {len(records)} records (offset={offset}, total matching={total_count}, accumulated={len(all_records)})")

        if len(records) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return all_records


def display_name(platform_id: str) -> str:
    """Return human-readable name if mapped, otherwise the raw ID."""
    return PLATFORM_NAMES.get(platform_id, platform_id)


def analyze_trades(records: list[dict]):
    """Analyze trades and produce platform trade counts."""
    # Count trades per platform (a platform gets +1 for each trade it appears in)
    platform_trades = defaultdict(int)
    # Track buyer vs seller breakdown
    platform_as_buyer = defaultdict(int)
    platform_as_seller = defaultdict(int)
    # Self-trades: same platform on both sides
    self_trades = []

    for r in records:
        buyer_platform = r.get("platformIdBuyer", "")
        seller_platform = r.get("platformIdSeller", "")

        if buyer_platform:
            platform_trades[buyer_platform] += 1
            platform_as_buyer[buyer_platform] += 1

        if seller_platform:
            platform_trades[seller_platform] += 1
            platform_as_seller[seller_platform] += 1

        # Flag self-trades
        if buyer_platform and seller_platform and buyer_platform == seller_platform:
            self_trades.append({
                "transactionId": r.get("transactionId"),
                "orderItemId": r.get("orderItemId"),
                "platform": buyer_platform,
                "tradeTime": r.get("tradeTime"),
            })

    return platform_trades, platform_as_buyer, platform_as_seller, self_trades


def print_report(records, platform_trades, platform_as_buyer, platform_as_seller, self_trades):
    """Print the formatted report."""
    print(f"\n{'=' * 90}")
    print(f"  PLATFORM TRADE REPORT")
    print(f"  Total trades in ledger: {len(records)}")
    print(f"  Unique platforms: {len(platform_trades)}")
    print(f"{'=' * 90}\n")

    # Sort by total trades descending
    sorted_platforms = sorted(platform_trades.items(), key=lambda x: x[1], reverse=True)

    # Column widths
    name_w = max(len(display_name(p)) for p, _ in sorted_platforms) if sorted_platforms else 20
    name_w = max(name_w, len("Platform"))

    header = f"  {'Platform':<{name_w}}  {'Total':>7}  {'As Buyer':>10}  {'As Seller':>10}  {'Platform ID'}"
    print(header)
    print(f"  {'-' * (name_w + 50)}")

    for platform_id, total in sorted_platforms:
        name = display_name(platform_id)
        buyer = platform_as_buyer.get(platform_id, 0)
        seller = platform_as_seller.get(platform_id, 0)
        # Show raw ID only if we have a name mapping (otherwise name IS the ID)
        id_col = f"  ({platform_id})" if platform_id in PLATFORM_NAMES else ""
        print(f"  {name:<{name_w}}  {total:>7}  {buyer:>10}  {seller:>10}{id_col}")

    print(f"\n  {'─' * 60}")
    print(f"  Total trade appearances: {sum(platform_trades.values())}")
    print(f"  (Each trade has a buyer platform + seller platform, so this can be up to 2× trade count)\n")

    # Self-trades
    if self_trades:
        print(f"{'=' * 90}")
        print(f"  ⚠ SELF-TRADES: {len(self_trades)} trade(s) where same platform is BOTH buyer and seller")
        print(f"{'=' * 90}\n")
        for st in self_trades[:20]:  # show first 20
            print(f"  Platform:      {display_name(st['platform'])} ({st['platform']})")
            print(f"  Transaction:   {st['transactionId']} / {st['orderItemId']}")
            print(f"  Trade Time:    {st['tradeTime']}")
            print()
        if len(self_trades) > 20:
            print(f"  ... and {len(self_trades) - 20} more self-trades\n")
    else:
        print("  No self-trades found (no platform appears as both buyer and seller).\n")


def main():
    parser = argparse.ArgumentParser(
        description="Count trades per platform from the DEG Ledger"
    )
    parser.add_argument(
        "--from-date", required=True,
        help="Start date (ISO 8601, e.g. 2026-03-01 or 2026-03-01T00:00:00Z)"
    )
    parser.add_argument(
        "--to-date", default=None,
        help="End date (ISO 8601, optional — defaults to now)"
    )
    parser.add_argument(
        "--ledger-url",
        default=os.environ.get("LEDGER_URL"),
        help="Base URL of the ledger API. Falls back to LEDGER_URL env var."
    )
    parser.add_argument(
        "--proxy", action="store_true",
        help="Use local proxy at localhost:8080 (server.py must be running). "
             "Note: proxy enforces 10-day lookback."
    )
    args = parser.parse_args()

    # Normalize dates
    from_date = args.from_date
    if len(from_date) == 10:  # bare date like 2026-03-01
        from_date += "T00:00:00.000Z"
    elif not from_date.endswith("Z"):
        from_date += "Z"

    to_date = args.to_date
    if to_date:
        if len(to_date) == 10:
            to_date += "T23:59:59.000Z"
        elif not to_date.endswith("Z"):
            to_date += "Z"
    else:
        # Server defaults to tradeTimeFrom + LEDGER_DATE_RANGE_DAYS (10) when
        # tradeTimeTo is omitted, so always send an explicit upper bound.
        to_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    if not args.proxy and not args.ledger_url:
        parser.error("--ledger-url is required (or set LEDGER_URL env var), or use --proxy")

    print(f"\nFetching trades from {from_date}" + (f" to {to_date}" if to_date else " to now") + "...\n")

    records = fetch_all_trades(from_date, to_date, args.proxy, args.ledger_url)

    if not records:
        print("No trades found for the given date range.")
        return

    platform_trades, as_buyer, as_seller, self_trades = analyze_trades(records)
    print_report(records, platform_trades, as_buyer, as_seller, self_trades)


if __name__ == "__main__":
    main()
