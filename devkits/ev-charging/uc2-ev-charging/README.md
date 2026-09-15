# EV Charging uc2 — Settlement-first Charging

A Beckn v2.0 LTS devkit for interoperable EV charging where **walk-in** and **reservation** contracts share one virtual queue, and the invoice is computed from the session ledger by a policy both parties run.

- **Design rationale, state machine, formulas and detours from the blueprint:** [DESIGN.md](./DESIGN.md)
- **Background:** [Thoughts on an interoperable EV charging network](https://ameetdesh.blogspot.com/2026/09/thoughts-on-interoperable-ev-charging.html)

This use case is self-contained: it runs `fidedocker/onix-adapter-deg:v2` from its own [`install/`](./install/) and [`config/`](./config/), separate from uc1, which uses the older adapter and payload shape. The shared stack topology, ngrok, and hosting notes are in [../../README.md](../../README.md).

## Scenario

EcoPower publishes one charging pool at its BTM Hub (CCS2 DC, up to 60 kW) with two offers:

| Offer | Mode | Terms (INR) |
|---|---|---|
| `ecopower-btm-walk-in` | `WALK_IN` | energy 18/kWh · occupancy 2/min · idle 10/min beyond 5 min grace · 2 demotions · grid delay credit 1/min |
| `ecopower-btm-reservation` | `RESERVATION` | the same, plus fee 100 · free cancellation up to 60 min before · CPO delay credit 5/min · cap 500 |

A driver reserves 18:00 at noon. The stall is assigned at 18:12, a grid event halves the power for 10 minutes, a charger fault stops it for 4, and the driver idles 9 minutes. The ledger settles at **600.00 INR**.

## Quick start

```bash
cd devkits/ev-charging/uc2-ev-charging/install
docker compose up -d
cd ../workflows
./run-arazzo.sh
```

Stop any other devkit stack first, because they share host ports 8081, 8082 and 9000.

| Workflow | What it shows | Outcome |
|---|---|---|
| `publish-catalog` | Pool + walk-in and reservation offers | ACK |
| `discover` | Filter by connector and mode | ACK |
| `reservation-session` | select → init → confirm (sandbox callbacks) → ASSIGNED → DEPARTED | 10 flows injected; driver pays 600.00 |
| `walk-in-session` | Demotion, 24 kWh, idle | 6 flows; driver pays 522.00 |
| `reservation-cancellation` | Cancel 30 min before start | 2 flows; fee 100.00 forfeited |
| `reservation-too-soon` | Reservation 40 min ahead | **400**, network policy N3 |
| `early-no-show` | NO_SHOW after 1 of 2 demotions | **400**, contract policy C2 |

## Payloads in one glance

| Step | The driver app sends | The CPO answers with |
|---|---|---|
| `select` | the chosen offer **copied verbatim**, the pool id with kWh needed, `vehicle` (+ `reservedStart`), `contractAttributes` copied from the offer with `driver` bound | the same contract + `quote` (`promisedKW`, `estimatedStart`) |
| `init` | the `on_select` contract, unchanged | the same |
| `confirm` | the `on_init` contract, unchanged | `contract.id`, `ACTIVE`, ledger `[QUEUED]` |
| — | — | `on_status` with the ledger grown by one row per state change |
| `cancel` | the confirmed contract | ledger ending `CANCELLED` + settlement |

The session ledger is a transition log:

```json
"ledger": [
  {"at": "2026-10-02T12:05:00Z", "state": "QUEUED"},
  {"at": "2026-10-02T18:12:00Z", "state": "ASSIGNED", "stallId": "IN*ECO*E01BTM*A1"},
  {"at": "2026-10-02T18:15:00Z", "state": "CHARGING", "kWh": 10.0},
  {"at": "2026-10-02T18:25:00Z", "state": "LIMITED_BY_GRID", "kWh": 5.0, "eventId": "BESCOM-DR-2026-10-02-1825"},
  {"at": "2026-10-02T18:35:00Z", "state": "LIMITED_BY_CPO", "kWh": 0},
  {"at": "2026-10-02T18:39:00Z", "state": "CHARGING", "kWh": 16.0},
  {"at": "2026-10-02T18:55:00Z", "state": "IDLE"},
  {"at": "2026-10-02T19:04:00Z", "state": "DEPARTED"}
]
```

Once the ledger is terminal, both adapters write the settlement into `contract.consideration[id=settlement]`. Each line is a net-zero pair:

```json
"considerationAttributes": {
  "@context": "https://schema.nfh.global/RevenueFlow/v2.0/context.jsonld", "@type": "RevenueFlow",
  "revenueFlows": [
    {"role": "driver", "value": -558, "currency": "INR", "description": "energy: 31 kWh at 18 INR/kWh"},
    {"role": "cpo", "value": 558, "currency": "INR", "description": "energy: 31 kWh at 18 INR/kWh"},
    {"role": "driver", "value": -62, "currency": "INR", "description": "occupancy: 31 min at 2 INR/min (40 min on stall, 4 added by CPO limits, 5 by grid limits)"},
    {"role": "cpo", "value": 62, "currency": "INR", "description": "occupancy: 31 min at 2 INR/min (40 min on stall, 4 added by CPO limits, 5 by grid limits)"},
    {"role": "driver", "value": -40, "currency": "INR", "description": "idle: 4 min beyond 5 min grace at 10 INR/min"},
    {"role": "cpo", "value": 40, "currency": "INR", "description": "idle: 4 min beyond 5 min grace at 10 INR/min"},
    {"role": "cpo", "value": -55, "currency": "INR", "description": "CPO delay credit: 11 min (7 late start beyond grace, 4 added by CPO limits) at 5 INR/min, cap 500"},
    {"role": "driver", "value": 55, "currency": "INR", "description": "CPO delay credit: 11 min (7 late start beyond grace, 4 added by CPO limits) at 5 INR/min, cap 500"},
    {"role": "cpo", "value": -5, "currency": "INR", "description": "grid delay credit: 5 min added by grid events at 1 INR/min"},
    {"role": "driver", "value": 5, "currency": "INR", "description": "grid delay credit: 5 min added by grid events at 1 INR/min"}
  ]
}
```

## Schemas

| Schema | Slot | Carries |
|---|---|---|
| [EvChargingService v2.0](../../../specification/schema/EvChargingService/v2.0/) | `resources[].resourceAttributes` | Charging pool: connector, power, site |
| [EvChargingOffer v3.0](../../../specification/schema/EvChargingOffer/v3.0/) | `offers[].offerAttributes` | `mode`, `terms`, contract template |
| [EvChargingCommitment v1.0](../../../specification/schema/EvChargingCommitment/v1.0/) | `commitments[].commitmentAttributes` | `vehicle`, `reservedStart`, `quote` |
| [EvChargingSession v3.0](../../../specification/schema/EvChargingSession/v3.0/) | `performance[].performanceAttributes` | `ledger` |
| [DEGContract v2.0](../../../specification/schema/DEGContract/v2.0/) | `contractAttributes` | roles `driver` / `cpo`, policy reference |
| [RevenueFlow v2.0](../../../specification/schema/RevenueFlow/v2.0/) | `consideration[].considerationAttributes` | Injected settlement |

New schemas and both policies are resolved from `https://raw.githubusercontent.com/ameetdesh/DEG/refs/heads/main/specification/…`.

## Policies

| Layer | File | Runs as |
|---|---|---|
| Network (structure, N1–N8) | [ev-charging-networkpolicy.rego](../../../specification/policies/ev-charging-networkpolicy.rego) | `checkPolicy` on all four modules, via [config/opa-network-policies.yaml](./config/opa-network-policies.yaml) |
| Contract (settlement, C1–C3) | [ev-charging-contractpolicy.rego](../../../specification/policies/ev-charging-contractpolicy.rego) | `contractpolicyenforcer`: enforced on every leg; injected at BPP caller and BAP receiver on `on_status` / `on_cancel` |

Run the unit tests with:

```bash
cd specification/policies
opa test ev-charging-contractpolicy.rego ev-charging-networkpolicy.rego test/ev-charging-contractpolicy_test.rego test/ev-charging-networkpolicy_test.rego
```

## Postman

[`postman/`](./postman/) holds `ev-charging-uc2-ev-charging.BAP-DEG` (driver app requests) and `.BPP-DEG` (CPO responses, catalog publish, ledger pushes). Regenerate them with `postman/generate.sh`. Requests keep the scenario's literal timestamps, because network rule N3 compares `reservedStart` with `context.timestamp`.

## Editing examples

Examples and sandbox fixtures are generated. Change the scenario facts in [`scripts/build_examples.py`](./scripts/build_examples.py), then:

```bash
python3 devkits/ev-charging/uc2-ev-charging/scripts/build_examples.py
devkits/ev-charging/uc2-ev-charging/postman/generate.sh
```
