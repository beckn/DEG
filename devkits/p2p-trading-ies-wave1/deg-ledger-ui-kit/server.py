#!/usr/bin/env python3
"""
DEG Ledger Dashboard server.
Serves index.html and proxies /api/ledger/get to the remote ledger API
(avoids browser CORS restrictions).

Requests are signed using Ed25519 + BLAKE2-512 per the Beckn protocol spec.

Setup:
    1. cp example.env .env
    2. Edit .env with your SUBSCRIBER_ID, RECORD_ID, SIGNING_PRIVATE_KEY, and LEDGER_URL
    3. pip install -r requirements.txt
    4. python3 server.py --ledger-url https://example.com (needed if LEDGER_URL not set in .env)
    5. Open http://localhost:8080

Querying via the proxy (no auth header needed — the server signs for you):

    curl -s -X POST http://localhost:8080/api/ledger/get \
      -H 'Content-Type: application/json' \
      -d '{"discomIdBuyer":"BESCOM","sort":"tradeTime","sortOrder":"desc","limit":10}'
"""

import argparse
import base64
import hashlib
import http.server
import json
import ssl
import time
import urllib.request
import os
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env file if present (simple loader, no dependency needed)
_env_path = os.path.join(DIR, ".env")
if os.path.isfile(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())

# ── Ledger API (set via --ledger-url or LEDGER_URL env var) ──
LEDGER_URL = None  # populated in main()
LEDGER_API = None

# ── Beckn signing config ──
SUBSCRIBER_ID = os.environ.get("SUBSCRIBER_ID")
UNIQUE_KEY_ID = os.environ.get("RECORD_ID")
SIGNING_PRIVATE_KEY = os.environ.get("SIGNING_PRIVATE_KEY")
EXPIRY_SECONDS = 300  # 5 minutes

# ── Max lookback window (0 = unlimited) ──
MAX_LOOKBACK_DAYS = 0

# ── Feature flags ──
SHOW_PARTICIPANT_IDS = os.environ.get("SHOW_PARTICIPANT_IDS", "false").lower() == "true"

# Pre-load private key once at startup
_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(
    base64.b64decode(SIGNING_PRIVATE_KEY)
)


def sign_payload(body: bytes) -> str:
    """
    Sign a request body and return the Authorization header value.

    Algorithm (mirrors beckn-signing-kit/nodejs/signer.js):
      1. BLAKE2b-512 hash of body → base64
      2. Build signing string:
           (created): <unix_ts>
           (expires): <unix_ts + 300>
           digest: BLAKE-512=<hash>
      3. Ed25519 sign the signing string
      4. Format Signature header
    """
    # 1. BLAKE2b-512 digest
    digest = hashlib.blake2b(body, digest_size=64).digest()
    digest_b64 = base64.b64encode(digest).decode()

    # 2. Signing string
    created = int(time.time())
    expires = created + EXPIRY_SECONDS
    signing_string = (
        f"(created): {created}\n"
        f"(expires): {expires}\n"
        f"digest: BLAKE-512={digest_b64}"
    )

    # 3. Ed25519 signature
    signature = _PRIVATE_KEY.sign(signing_string.encode())
    sig_b64 = base64.b64encode(signature).decode()

    # 4. Authorization header
    return (
        f'Signature keyId="{SUBSCRIBER_ID}|{UNIQUE_KEY_ID}|ed25519"'
        f',algorithm="ed25519"'
        f',created="{created}"'
        f',expires="{expires}"'
        f',headers="(created) (expires) digest"'
        f',signature="{sig_b64}"'
    )


def enforce_lookback(body: bytes) -> bytes:
    """
    If MAX_LOOKBACK_DAYS > 0, ensure the request body includes a tradeTimeFrom
    no older than that many days ago.  If 0, pass the client payload through
    as-is (the client is responsible for sending its own date range).
    """
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    if MAX_LOOKBACK_DAYS > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_LOOKBACK_DAYS)
        cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Only tighten — never widen — the window
        existing = payload.get("tradeTimeFrom")
        if not existing or existing < cutoff_iso:
            payload["tradeTimeFrom"] = cutoff_iso

    return json.dumps(payload, separators=(",", ":")).encode()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self, *args, **kwargs):
        if self.path == "/api/config":
            data = json.dumps({"showParticipantIds": SHOW_PARTICIPANT_IDS}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET(*args, **kwargs)

    def do_POST(self):
        if self.path == "/api/ledger/get":
            self._proxy_ledger()
        else:
            self.send_error(404)

    def _proxy_ledger(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"

            # Enforce 10-day lookback window
            body = enforce_lookback(body)

            # Sign the payload
            auth_header = sign_payload(body)

            req = urllib.request.Request(
                LEDGER_API,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": auth_header,
                },
                method="POST",
            )
            # Allow self-signed / sslip.io certs
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, context=ctx) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            err = json.dumps({"error": str(e)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def log_message(self, fmt, *args):
        # Compact logging
        print(f"[{self.log_date_time_string()}] {fmt % args}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DEG Ledger Dashboard server")
    parser.add_argument(
        "--ledger-url",
        default=os.environ.get("LEDGER_URL"),
        help="Base URL of the ledger API (e.g. https://example.com). "
             "Falls back to LEDGER_URL env var.",
    )
    args = parser.parse_args()

    if not args.ledger_url:
        parser.error("--ledger-url is required (or set LEDGER_URL env var)")

    LEDGER_URL = args.ledger_url.rstrip("/")
    LEDGER_API = f"{LEDGER_URL}/ledger/get"

    server = http.server.HTTPServer(("", PORT), Handler)
    print(f"DEG Ledger Dashboard running at http://localhost:{PORT}")
    print(f"Proxying to {LEDGER_API}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
