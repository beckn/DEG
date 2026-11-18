# EV Charging Devkit

Beckn Protocol 2.0 LTS (`core-v2.0.0-lts`) devkit for EV charging between an EV driver app (BAP) and a charge point operator platform (BPP).

For the shared stack topology, prerequisites, transaction flow, hosting, ngrok notes and cleanup, see [../README.md](../README.md).

## Two ways to run it

| Mode | Command (in `install/`) | Backends | Use it to |
|---|---|---|---|
| **Sandbox** | `docker compose up -d` | `sandbox-bap` / `sandbox-bpp` reply with fixed LTS payloads | check your own payloads and adapter config with the Arazzo workflows or Postman |
| **Apps** | `docker compose -f docker-compose.yml -f docker-compose.apps.yml up -d` | the [reference apps](./reference-apps): a consumer app and a CPO platform with real state | run every use case end to end as live transactions; see a working BAP and BPP |

Both modes run Beckn ONIX 1.9.4 for both participants, with signing, DeDi registry checks and LTS schema validation on.

## Use cases

| Use case | BAP (consumer) | BPP (provider) | Examples / workflow |
|---|---|---|---|
| [uc1-ev-charging](./uc1-ev-charging/) | EV driver app | Charge point operator | [examples](./uc1-ev-charging/examples/), [Arazzo](./uc1-ev-charging/workflows/ev-charging.arazzo.yaml) |

Covered, each as a runnable flow:

- **Walk-in:** scan the charger QR, pay through the CPO's payment link, charge, live telemetry, stop, final bill, invoice, rate, support.
- **Reservation:** search by area, connector and power; quote with surge, discount and fees; pay in the consumer app; start at the slot; track.
- **Discovery:** by EVSE, CPO, station, radius, opening hours, connector spec, vehicle spec.
- **Exceptions:**
  - slot already booked;
  - outstanding balance carried to the next quote;
  - start refused (EVSE inoperative);
  - power cut (bill delivered energy, refund the rest);
  - charger offline and overcharging;
  - battery full early;
  - invoice ready.
- **Cancellation:** preview the terms (`context.try`), consumer cancellation with or without a late fee, CPO-initiated cancellation with a full refund.
- **Support:** ticket opened and resolved by the CPO.
- **Business side** (apps mode): publishing a new site to discovery, and the operator dashboard (sessions, revenue, dues, faults, tickets).

The canonical examples, the conventions they follow and the field map from the earlier `message.order` shape are in [examples/ev-charging/v2](../../examples/ev-charging/v2/README.md).

## Run the use cases (apps mode)

```bash
cd install
docker compose -f docker-compose.yml -f docker-compose.apps.yml up -d
python3 ../reference-apps/scenarios/run-usecases.py --iterations 3
```

The runner drives every use case through the consumer app as real transactions. It checks each outcome against independently computed values (quotes, bills, refunds, dues, error codes, discovery results), then prints a table of transactions per use case and per-action latency.

- **Consumer app:** http://localhost:3001
- **CPO operations dashboard:** http://localhost:3002

`python3 ../reference-apps/scenarios/audit-messages.py` counts every message both apps sent and received.

## Run the Arazzo workflows (either mode)

```bash
cd uc1-ev-charging/workflows
./run-arazzo.sh                 # all six workflows
./run-arazzo.sh -w walk-in -v   # one workflow
```

Workflows: `discover`, `walk-in`, `reservation`, `exceptions`, `cancellation`, `support`.

## Network configuration

| Parameter | Value |
|---|---|
| Network id (`context.networkId`) | `nfh.global/testnet-evcharging` |
| BAP id | `bap.example.com` (test keys in `config/local-ev-bap.yaml`, registered on DeDi for this network) |
| BPP id | `bpp.example.com` (test keys in `config/local-ev-bpp.yaml`) |
| BAP / BPP host (router) | `http://beckn-router:9000` |
| BAP adapter caller | `http://localhost:8081/bap/caller` |
| BPP adapter caller | `http://localhost:8082/bpp/caller` |
| Discovery (sandbox mode) | the hosted fabric discovery service; its callbacks need a public `bapUri` (ngrok, see ../README.md) |
| Discovery (apps mode) | the CPO platform's local discovery service, through the BPP adapter |

A different `networkId` is rejected by the BPP adapter with `AUT_NETWORK_NOT_ALLOWED`, because the example participants' DeDi records list only their member networks.

## Notes

- **Local schema copies.** `schemas/` holds `EvChargingService`, `EvChargingOffer`, `EvChargingSession` and `EvChargingPointOperator` v2.0, named by their `@type`, because ONIX's local schema mode looks packs up by `@type`. The adapters preload them (`extendedSchema_localSchemaPath`) because the copies on schema.nfh.global still have broken `$ref`s. Remove the preload once the fixed packs are published.
- **Mock replies.** `install/sandbox-fixtures/` supplies LTS `on_*` replies for the mock CPO, because the replies built into the `fidedocker/sandbox-2.0` image predate LTS.
- **Postman.** Regenerate the collections from the examples with `python3 scripts/generate_postman_collection.py --role BAP|BPP`.

## Related

- [Reference apps](./reference-apps/README.md)
- [EV charging implementation guide](../../docs/implementation-guides/v2/EV_Charging/EV_Charging.md)
- [Migration kit](../ev-charging-migration-kit/), for apps still on the earlier `message.order` shape
- [Data Exchange Devkit](../data-exchange/)
