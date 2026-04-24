# DEG Ledger UI Kit

A lightweight dashboard and CLI toolkit for viewing and querying the DEG (Digital Energy Grid) trade ledger. All requests are signed using Ed25519 + BLAKE2-512 per the Beckn protocol spec.

## Access Control

The ledger service enforces **role-based access control** — a caller (trading platform or DISCOM) can only see trades where they are a party. Your `SUBSCRIBER_ID` determines which records are visible to you.

## DISCOM Subscriber ID to Acronym

Trades in the ledger use short DISCOM acronyms. The mapping from Beckn subscriber ID to acronym (as configured in [deg-ledgr-service](https://github.com/beckn/deg-ledgr-service)):

| Subscriber ID | DISCOM Acronym | Full Name |
|---|---|---|
| `ev-charging-sandbox1.krypc.com` | TPDDL | Tata Power Delhi Distribution Limited |
| `dev-deg-bap.powerxchange.io` | PVVNL | Paschimanchal Vidyut Vitran Nigam Limited |
| `bsesdelhi.com` | BRPL | BSES Rajdhani Power Limited |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials
cp example.env .env
# Edit .env with your SUBSCRIBER_ID, RECORD_ID, SIGNING_PRIVATE_KEY, and LEDGER_URL

# 3. Start the dashboard server
python server.py --ledger-url https://<your-ledger-api-url>

# 4. Open http://localhost:8080 in your browser
```

> If `LEDGER_URL` is set in `.env`, the `--ledger-url` flag can be omitted.

## Scripts

| Script | Purpose |
|---|---|
| **`server.py`** | Serves the dashboard UI (`index.html`) on port 8080. Proxies `/api/ledger/get` requests to the remote ledger API, signing each request server-side so the browser avoids CORS issues. |
| **`generate_curls.py`** | Generates ready-to-run, signed `curl` commands for the ledger API endpoints (`/ledger/get`, `/ledger/put`, `/ledger/record`). Useful for debugging or scripting outside the UI. |
| **`platform_trade_report.py`** | CLI report that fetches all trades in a date range and prints per-platform trade counts (buyer + seller appearances), flagging self-trades. |
| **`index.html`** | Single-page dashboard UI served by `server.py`. Displays trade data in a filterable, sortable table. |

## Querying via curl

With `server.py` running, you can query the ledger via `localhost:8080` — no auth header needed, the server signs requests for you.

```bash
# Fetch latest 10 trades for a buyer DISCOM
curl -s -X POST http://localhost:8080/api/ledger/get \
  -H 'Content-Type: application/json' \
  -d '{"discomIdBuyer":"BESCOM","sort":"tradeTime","sortOrder":"desc","limit":10}'

# Trades in a date range
curl -s -X POST http://localhost:8080/api/ledger/get \
  -H 'Content-Type: application/json' \
  -d '{"discomIdBuyer":"BESCOM","tradeTimeFrom":"2026-03-01T00:00:00.000Z","tradeTimeTo":"2026-03-31T23:59:59.000Z"}'

# Trades between two DISCOMs
curl -s -X POST http://localhost:8080/api/ledger/get \
  -H 'Content-Type: application/json' \
  -d '{"discomIdBuyer":"BESCOM","discomIdSeller":"TPDDL","sort":"tradeTime","sortOrder":"desc"}'

# Lookup a specific trade by recordId
curl -s -X POST http://localhost:8080/api/ledger/get \
  -H 'Content-Type: application/json' \
  -d '{"recordId":"TXN-2026-001_ITEM-42"}'
```

Pipe through `jq` for pretty output: `curl ... | jq .`

For **signed curls against the remote API directly** (bypassing the proxy), use `generate_curls.py`:

```bash
python generate_curls.py --ledger-url https://<your-ledger-api-url> get
```

## Configuration (`.env`)

| Variable | Description |
|---|---|
| `SUBSCRIBER_ID` | Your Beckn subscriber ID |
| `RECORD_ID` | Your Beckn registry record ID |
| `SIGNING_PRIVATE_KEY` | Base64-encoded Ed25519 private key for request signing |
| `LEDGER_URL` | Base URL of the ledger API |
| `SHOW_PARTICIPANT_IDS` | Show buyerId/sellerId columns in the UI (`true`/`false`, default `false`) |

## API Specification

The DEG Ledger API spec (OpenAPI) is at [`../../../../specification/api/deg_contract_ledger.yaml`](../../../../specification/api/deg_contract_ledger.yaml). It documents the `/ledger/get`, `/ledger/put`, and `/ledger/record` endpoints, including request/response schemas, role-based write permissions, and field-level access control rules.
