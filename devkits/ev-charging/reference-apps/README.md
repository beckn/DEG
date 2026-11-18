# EV charging reference apps (Beckn 2.0 LTS)

A consumer app (BAP) and a charge point operator platform (BPP) that run every EV charging use case as live Beckn transactions through the devkit's two ONIX adapters. Python standard library only; no other dependencies.

```
 driver / runner ──▶ consumer app :3001 ──▶ onix-bap ──▶ beckn-router ──▶ onix-bpp ──▶ CPO platform :3002
                    (bap-app)        ◀── callbacks ◀──────────────── on_* ◀──────────── (cpo-app)
```

Every request and callback is signed, checked against the DeDi registry and validated against the LTS core spec and the EV attribute packs. A payload the apps get wrong is rejected by ONIX exactly as it would be on a live network.

## Start

```bash
cd ../install
docker compose -f docker-compose.yml -f docker-compose.apps.yml up -d
```

- **Consumer app:** http://localhost:3001. Find chargers near you or scan a QR (charger id), get a quote, pay (UPI link or in-app), start, see the live meter, stop, then get the receipt and invoice, rate, ask for support, or cancel.
- **CPO operations:** http://localhost:3002. Sessions, revenue, outstanding dues, faults and tickets; buttons to mark an EVSE inoperative, cut power, take the charger's CMS link offline, cancel a booking, or resolve a ticket.

## What each app does

**CPO platform (`cpo-app/`)**

- **Catalog:** serves the catalogs in `uc1-ev-charging/examples/02_on_discover` (three CPOs in Bengaluru).
- **Local discovery service** (apps mode): answers `discover` with the same filter and spatial conventions as the fabric discovery service, and accepts `catalog/publish`.
- **Quote:** energy cost, a 20% surge, a 15% offer discount, a 10 INR service fee, an overcharge estimate (0.3 kWh, refunded if unused), a 2.5% buyer finder fee, and any outstanding balance from an earlier session.
- **Slots:** reservations, with overlap checks (`BIZ_FULFILLMENT_UNAVAILABLE`).
- **Payment collection:**
  - *by the CPO:* a payment link (`/pay/<transaction>`), then an unsolicited `on_status` when it's paid;
  - *by the consumer app:* settlement accounts are shared in `on_init`, and the consumer app reports `COMPLETED` in `confirm`.
- **Meter:** accelerated, with telemetry (state of charge, power, energy, voltage, current) on `status` and `track`.
- **Final bill on stop**, with three outcomes:
  - *refund:* the unused estimate and any undercharge come back as a `REFUNDED` settlement to the buyer;
  - *dues:* an overcharge beyond the estimate becomes a `PENDING` settlement, and the balance appears on the buyer's next quote;
  - *invoice:* an `on_update` with the invoice document follows.
- **Faults:**
  - *EVSE inoperative:* start is refused, with an `EVSE_INOPERATIVE` cause;
  - *power cut:* an unsolicited `INTERRUPTED` status, with the session billed for the energy delivered and the rest refunded;
  - *CMS offline:* the charger keeps dispensing past the booked energy (overcharge).
- **Cancellation:**
  - *terms:* `context.try` returns the terms and the refund without cancelling;
  - *consumer cancellation:* free up to 30 minutes before the slot, a 10% fee after that;
  - *CPO cancellation:* unsolicited, with a full refund.
- **Support and rating:** support tickets, resolved by the CPO with an unsolicited `on_support`; ratings; live tracking handles.

**Consumer app (`bap-app/`)**

- **One endpoint per user action:** a JSON API (`POST /api/<op>`: `discover`, `select`, `init`, `pay`, `confirm`, `status`, `start`, `stop`, `track`, `cancel`, `rate`, `support`). Each sends one Beckn request and returns the matching callback.
- **Unsolicited callbacks:** `POST /api/wait` waits for one (payment received, power cut, CPO cancellation, invoice, ticket resolved).
- **History:** `GET /api/session/<transaction>` shows the transaction's history; `GET /api/messages` lists every message sent and received.

## Use cases and the success metric

`scenarios/run-usecases.py` runs 14 use cases as transactions. The success metric is transactions that complete with every assertion holding:
- both adapters ACK every leg;
- the business outcome matches values computed independently in the runner (quote and bill arithmetic, refunds, dues, error codes, discovery results).

| Code | Use case |
|---|---|
| UC-01 | Walk-in: QR, payment link, charge, live telemetry, track, stop, invoice, rate, support |
| UC-02 | Reservation: area + connector search, in-app payment, slot, charge, invoice |
| UC-03 | Discovery: every example intent, text search, `S_DWITHIN` 1 km, and `S_WITHIN` with a point (must return nothing) |
| UC-04 | Slot conflict between two drivers |
| UC-05 | Overcharge beyond the estimate becomes dues and is collected on the next booking |
| UC-06 | Start refused (EVSE inoperative), fault cleared, retry succeeds |
| UC-07 | Power cut mid-session: interrupted, billed for energy delivered, rest refunded |
| UC-08 | Charger offline overcharge within the estimate |
| UC-09 | Battery full early: billed for 2.0 kWh, refund |
| UC-10 | Consumer cancellation: terms preview, then free (2 h ahead) or with a late fee (10 min ahead) |
| UC-11 | CPO cancellation with a full refund |
| UC-12 | Support ticket opened after a session and resolved by the CPO |
| UC-13 | CPO publishes a new site; discovery finds it |
| UC-14 | Invalid transitions (stop before start, cancel after completion) are refused |

```bash
python3 scenarios/run-usecases.py --iterations 10          # all use cases, 10 times
python3 scenarios/run-usecases.py --only UC-05,UC-07       # a subset
python3 scenarios/audit-messages.py --dump /tmp/ev-msgs    # count and dump every message sent
```

The runner resets the CPO platform before each iteration and writes `results/run-<time>.{json,md}`.

## Limits

- **In-memory state,** reset on restart. No database, no authentication on the operations API. These are reference apps, not production services.
- **Simulated payment** (the payment page marks the order paid) and an **accelerated, simulated meter** (`SIM_KWH_PER_SEC`).
- **Apps mode discovery is local.** It runs against the CPO platform's own discovery service. Against the hosted fabric discovery service, use sandbox mode with a public `bapUri`.
