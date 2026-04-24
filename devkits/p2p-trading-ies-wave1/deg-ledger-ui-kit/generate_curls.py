#!/usr/bin/env python3
"""
Generate signed curl commands for the DEG Ledger API.

Reads credentials from .env and produces ready-to-run curl commands
(printed, not executed) for /ledger/get, /ledger/put, and /ledger/record.

Usage:
    python3 generate_curls.py --ledger-url https://example.com
    python3 generate_curls.py --ledger-url https://example.com get
    python3 generate_curls.py --ledger-url https://example.com get '{"buyerId":"X"}'
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import time

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

# ── Config from env ──
SUBSCRIBER_ID = os.environ.get("SUBSCRIBER_ID", "p2p-trading-sandbox1.com")
RECORD_ID = os.environ.get("RECORD_ID", "76EU8aUqHouww7gawT6EibH4bseMCumyDv3sgyXSKENGk8NDcdVwmQ")
SIGNING_PRIVATE_KEY = os.environ.get("SIGNING_PRIVATE_KEY", "Pc6dkYo5LeP0LkwvZXVRV9pcbeh8jDdtdHWymID5cjw=")
LEDGER_URL = None  # populated in main()
EXPIRY_SECONDS = 300

_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(
    base64.b64decode(SIGNING_PRIVATE_KEY)
)


def sign_payload(body: bytes) -> str:
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

    signature = _PRIVATE_KEY.sign(signing_string.encode())
    sig_b64 = base64.b64encode(signature).decode()

    return (
        f'Signature keyId="{SUBSCRIBER_ID}|{RECORD_ID}|ed25519"'
        f',algorithm="ed25519"'
        f',created="{created}"'
        f',expires="{expires}"'
        f',headers="(created) (expires) digest"'
        f',signature="{sig_b64}"'
    )


def make_curl(endpoint: str, payload: dict) -> str:
    """Build a signed curl command string (not executed)."""
    url = f"{LEDGER_URL}{endpoint}"
    body = json.dumps(payload, separators=(",", ":"))
    auth = sign_payload(body.encode())

    return (
        f"curl -sk -X POST '{url}' \\\n"
        f"  -H 'Content-Type: application/json' \\\n"
        f"  -H 'Authorization: {auth}' \\\n"
        f"  -d '{body}'"
    )


def print_section(title: str, curls: list[tuple[str, str]]):
    """Print a titled section of curl examples."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")
    for label, curl in curls:
        print(f"\n--- {label} ---\n")
        print(curl)
        print()


# ═══════════════════════════════════════════════════════════════════════════════
#  /ledger/get  — query examples
# ═══════════════════════════════════════════════════════════════════════════════

def get_curls():
    examples = []

    # 1. All trades for a buyer discom within a trade-time window
    examples.append((
        "Trades for a buyer DISCOM in a trade-time window",
        make_curl("/ledger/get", {
            "discomIdBuyer": "BESCOM",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
        }),
    ))

    # 2. All trades for a seller discom within a trade-time window
    examples.append((
        "Trades for a seller DISCOM in a trade-time window",
        make_curl("/ledger/get", {
            "discomIdSeller": "TPDDL",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
        }),
    ))

    # 3. Trades for a discom with delivery-start-time gate
    examples.append((
        "Trades for a DISCOM with delivery-start-time window",
        make_curl("/ledger/get", {
            "discomIdBuyer": "BESCOM",
            "deliveryStartFrom": "2026-02-10T00:00:00.000Z",
            "deliveryStartTo": "2026-02-15T23:59:59.000Z",
            "sort": "deliveryStartTime",
            "sortOrder": "asc",
        }),
    ))

    # 4. Trades for a discom with BOTH trade-time AND delivery-start-time gates
    examples.append((
        "DISCOM trades filtered by both trade-time AND delivery-start-time gates",
        make_curl("/ledger/get", {
            "discomIdBuyer": "BESCOM",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
            "deliveryStartFrom": "2026-02-10T00:00:00.000Z",
            "deliveryStartTo": "2026-02-15T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
        }),
    ))

    # 5. Filter by buyerId
    examples.append((
        "Trades for a specific buyerId",
        make_curl("/ledger/get", {
            "buyerId": "CA-BESCOM-1234567",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
        }),
    ))

    # 6. Filter by sellerId
    examples.append((
        "Trades for a specific sellerId",
        make_curl("/ledger/get", {
            "sellerId": "DEG-TPDDL-87654321",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
        }),
    ))

    # 7. Filter by buyer platform
    examples.append((
        "Trades for a specific buyer platform (platformIdBuyer)",
        make_curl("/ledger/get", {
            "platformIdBuyer": "bap.energy-exchange.in",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
        }),
    ))

    # 8. Filter by seller platform
    examples.append((
        "Trades for a specific seller platform (platformIdSeller)",
        make_curl("/ledger/get", {
            "platformIdSeller": "bpp.solar-prosumer.in",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
        }),
    ))

    # 9. Filter by both buyer and seller discom
    examples.append((
        "Trades between two specific DISCOMs",
        make_curl("/ledger/get", {
            "discomIdBuyer": "BESCOM",
            "discomIdSeller": "TPDDL",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
        }),
    ))

    # 10. Combined: discom + platform + time gates + pagination
    examples.append((
        "Combined filters: DISCOM + platform + time gates + pagination",
        make_curl("/ledger/get", {
            "discomIdBuyer": "BESCOM",
            "platformIdBuyer": "bap.energy-exchange.in",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-15T23:59:59.000Z",
            "deliveryStartFrom": "2026-02-10T00:00:00.000Z",
            "deliveryStartTo": "2026-02-15T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
            "limit": 50,
            "offset": 0,
        }),
    ))

    # 11. Lookup by recordId
    examples.append((
        "Lookup a specific trade by recordId",
        make_curl("/ledger/get", {
            "recordId": "TXN-2026-001_ITEM-42",
        }),
    ))

    # 12. Lookup by transactionId + orderItemId
    examples.append((
        "Lookup by transactionId and orderItemId",
        make_curl("/ledger/get", {
            "transactionId": "TXN-2026-001",
            "orderItemId": "ITEM-42",
        }),
    ))

    # 13. Trades where both buyer and seller discom statuses are filled
    examples.append((
        "Trades with both DISCOM statuses filled (statusBuyerDiscom + statusSellerDiscom)",
        make_curl("/ledger/get", {
            "statusBuyerDiscom": "COMPLETED",
            "statusSellerDiscom": "COMPLETED",
            "tradeTimeFrom": "2026-02-01T00:00:00.000Z",
            "tradeTimeTo": "2026-02-16T23:59:59.000Z",
            "sort": "tradeTime",
            "sortOrder": "desc",
        }),
    ))

    print_section("POST /ledger/get  —  Query / Filter Examples", examples)


# ═══════════════════════════════════════════════════════════════════════════════
#  /ledger/put  — create record examples
# ═══════════════════════════════════════════════════════════════════════════════

def put_curls():
    examples = []

    examples.append((
        "Create a new ledger record (BUYER role)",
        make_curl("/ledger/put", {
            "role": "BUYER",
            "transactionId": "TXN-2026-001",
            "orderItemId": "ITEM-42",
            "platformIdBuyer": "bap.energy-exchange.in",
            "platformIdSeller": "bpp.solar-prosumer.in",
            "discomIdBuyer": "BESCOM",
            "discomIdSeller": "TPDDL",
            "buyerId": "CA-BESCOM-1234567",
            "sellerId": "DEG-TPDDL-87654321",
            "tradeTime": "2026-02-15T10:30:00.000Z",
            "deliveryStartTime": "2026-02-15T11:00:00.000Z",
            "deliveryEndTime": "2026-02-15T12:00:00.000Z",
            "tradeDetails": [
                {"tradeQty": 5.5, "tradeType": "ENERGY", "tradeUnit": "KWH"}
            ],
            "clientReference": "my-client-ref-001",
        }),
    ))

    examples.append((
        "Create a new ledger record (SELLER role)",
        make_curl("/ledger/put", {
            "role": "SELLER",
            "transactionId": "TXN-2026-001",
            "orderItemId": "ITEM-42",
            "platformIdBuyer": "bap.energy-exchange.in",
            "platformIdSeller": "bpp.solar-prosumer.in",
            "discomIdBuyer": "BESCOM",
            "discomIdSeller": "TPDDL",
            "buyerId": "CA-BESCOM-1234567",
            "sellerId": "DEG-TPDDL-87654321",
            "tradeTime": "2026-02-15T10:30:00.000Z",
            "deliveryStartTime": "2026-02-15T11:00:00.000Z",
            "deliveryEndTime": "2026-02-15T12:00:00.000Z",
            "tradeDetails": [
                {"tradeQty": 5.5, "tradeType": "ENERGY", "tradeUnit": "KWH"}
            ],
            "clientReference": "my-client-ref-002",
        }),
    ))

    print_section("POST /ledger/put  —  Create Record Examples", examples)


# ═══════════════════════════════════════════════════════════════════════════════
#  /ledger/record  — discom update examples
# ═══════════════════════════════════════════════════════════════════════════════

def record_curls():
    examples = []

    # Seller discom records actual pushed (Round 1)
    examples.append((
        "Seller DISCOM records ACTUAL_PUSHED (Round 1)",
        make_curl("/ledger/record", {
            "role": "SELLER_DISCOM",
            "transactionId": "TXN-2026-001",
            "orderItemId": "ITEM-42",
            "sellerFulfillmentValidationMetrics": [
                {"validationMetricType": "ACTUAL_PUSHED", "validationMetricValue": 5.2}
            ],
            "statusSellerDiscom": "PENDING",
            "clientReference": "sd-round1-001",
        }),
    ))

    # Buyer discom records actual pulled (Round 2)
    examples.append((
        "Buyer DISCOM records ACTUAL_PULLED (Round 2)",
        make_curl("/ledger/record", {
            "role": "BUYER_DISCOM",
            "transactionId": "TXN-2026-001",
            "orderItemId": "ITEM-42",
            "buyerFulfillmentValidationMetrics": [
                {"validationMetricType": "ACTUAL_PULLED", "validationMetricValue": 4.8}
            ],
            "statusBuyerDiscom": "COMPLETED",
            "clientReference": "bd-round2-001",
        }),
    ))

    # Seller discom final settlement (Round 3)
    examples.append((
        "Seller DISCOM final settlement (Round 3)",
        make_curl("/ledger/record", {
            "role": "SELLER_DISCOM",
            "transactionId": "TXN-2026-001",
            "orderItemId": "ITEM-42",
            "sellerFulfillmentValidationMetrics": [
                {"validationMetricType": "ACTUAL_PUSHED", "validationMetricValue": 4.8}
            ],
            "statusSellerDiscom": "COMPLETED",
            "clientReference": "sd-round3-001",
        }),
    ))

    # Cancel a trade (outage)
    examples.append((
        "Buyer DISCOM cancels trade due to outage",
        make_curl("/ledger/record", {
            "role": "BUYER_DISCOM",
            "transactionId": "TXN-2026-001",
            "orderItemId": "ITEM-42",
            "statusBuyerDiscom": "CANCELLED_OUTAGE",
            "clientReference": "bd-cancel-001",
        }),
    ))

    print_section("POST /ledger/record  —  DISCOM Update Examples", examples)


# ═══════════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════════

ENDPOINT_MAP = {
    "get": "/ledger/get",
    "put": "/ledger/put",
    "record": "/ledger/record",
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate signed curl commands for the DEG Ledger API")
    parser.add_argument(
        "--ledger-url",
        default=os.environ.get("LEDGER_URL"),
        help="Base URL of the ledger API (e.g. https://example.com). "
             "Falls back to LEDGER_URL env var.",
    )
    parser.add_argument("command", nargs="?", default="all", choices=["all", "get", "put", "record"],
                        help="Which endpoint examples to show (default: all)")
    parser.add_argument("payload", nargs="?", default=None,
                        help="Custom JSON payload (optional)")
    args = parser.parse_args()

    if not args.ledger_url:
        parser.error("--ledger-url is required (or set LEDGER_URL env var)")

    LEDGER_URL = args.ledger_url.rstrip("/")
    cmd = args.command
    custom_payload = args.payload

    print(f"Ledger API:     {LEDGER_URL}")
    print(f"Subscriber ID:  {SUBSCRIBER_ID}")
    print(f"Record ID:      {RECORD_ID}")
    print(f"Signatures expire in {EXPIRY_SECONDS}s — run the curl within that window.")

    # Custom payload mode: generate a single signed curl for the given method
    if custom_payload and cmd in ENDPOINT_MAP:
        try:
            payload = json.loads(custom_payload)
        except json.JSONDecodeError as e:
            print(f"\nError: invalid JSON payload — {e}")
            sys.exit(1)
        endpoint = ENDPOINT_MAP[cmd]
        print(f"\n--- Custom {endpoint} ---\n")
        print(make_curl(endpoint, payload))
        print()
        sys.exit(0)

    # Examples mode (no custom payload)
    if cmd in ("all", "get"):
        get_curls()
    if cmd in ("all", "put"):
        put_curls()
    if cmd in ("all", "record"):
        record_curls()
