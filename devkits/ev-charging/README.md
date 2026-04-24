# EV Charging Devkit

Beckn Protocol v2.0 devkit for EV charging flows between network actors (BAP — EV Driver App/Charging Finder, BPP — Charging Station Operator).

For the shared stack topology, prerequisites, Quick Start, transaction flow, hosting, ngrok notes, and cleanup, see [../README.md](../README.md).

## Use Cases

| Use Case | BAP (Consumer) | BPP (Provider) | Description |
|----------|---------------|----------------|-------------|
| [uc1-ev-charging](./uc1-ev-charging/) | EV Driver App | Charging Station Operator | Discovery → reserve → session → billing → cancellation |

The devkit covers:
- **Charging station discovery** — filter by location, connector, power rating, availability
- **Reservation and booking** — time-based and quantity-based slot reservation
- **Charging session management** — initiate, monitor, and complete with real-time status
- **Payment and billing** — pricing, tariffs, buyer finder fees, settlement
- **Support and cancellation** — support requests, cancellation, dispute handling

## Postman

`uc1-ev-charging/postman/ev-charging-uc1-ev-charging.{BAP,BPP}-DEG.postman_collection.json`. Collections are regenerated with `python3 scripts/generate_postman_collection.py --role BAP|BPP`.

## Network Configuration (defaults)

| Parameter | Value |
|-----------|-------|
| Domain | `beckn.one:deg:ev-charging:2.0.0` |
| BAP ID | `ev-charging.sandbox1.com` |
| BPP ID | `ev-charging.sandbox2.com` |
| BAP host (router) | `http://beckn-router:9000` |
| BPP host (router) | `http://beckn-router:9000` |
| BAP adapter caller | `http://localhost:8081/bap/caller` |
| BPP adapter caller | `http://localhost:8082/bpp/caller` |

## Related

- [EV Charging examples](./uc1-ev-charging/examples/) — organised by step (`01_discover/`, `02_on_discover/`, …)
- [EV Charging Arazzo workflow](./uc1-ev-charging/workflows/ev-charging.arazzo.yaml)
- [Data Exchange Devkit](../data-exchange/) — inline dataset delivery via DDM
