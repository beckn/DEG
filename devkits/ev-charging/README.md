# EV Charging Devkit

Beckn Protocol 2.0 LTS (`core-v2.0.0-lts`) devkit for EV charging between an EV driver app (BAP) and a charge point operator platform (BPP).

For the shared stack topology, prerequisites, transaction flow, hosting, ngrok notes and cleanup, see [../README.md](../README.md).

## Run it

Start the stack with `docker compose up -d` in `install/`. `sandbox-bap` and `sandbox-bpp` reply with fixed LTS payloads, so you can check your own payloads and adapter config with the Arazzo workflows or Postman.

The stack runs Beckn ONIX 1.9.4 for both participants, with signing, DeDi registry checks and LTS schema validation on.

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
- **Catalog publishing:** a CPO publishing a new site (example request only; the workflows do not send it, because the BPP adapter routes publish to the hosted fabric catalog service).

The canonical examples, the conventions they follow and the field map from the earlier `message.order` shape are in [examples/ev-charging/v2](../../examples/ev-charging/v2/README.md).

## Run the Arazzo workflows

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
| Discovery | the hosted fabric discovery service; its callbacks need a public `bapUri` (ngrok, see ../README.md) |

A different `networkId` is rejected by the BPP adapter with `AUT_NETWORK_NOT_ALLOWED`, because the example participants' DeDi records list only their member networks.

## Notes

- **Local schema copies (temporary).** `schemas/` holds `EvChargingService`, `EvChargingOffer`, `EvChargingSession` and `EvChargingPointOperator` v2.0. The adapters preload them (`extendedSchema_localSchemaPath`) because the copies on schema.nfh.global still have broken `$ref`s. Remove the preload, and the `../schemas` mount it needs, once the fixed packs are published.
  - **Named by `@type`:** the folders use the `@type` because ONIX's local schema mode looks packs up by `@type`.
  - **Two side effects in ONIX 1.9.4:**
    - In local mode, ONIX re-parses the pack and re-fetches its remote `$ref`s for every object. That is why `discover` (many objects) takes about 1.5 s, against about 60 ms for every other action.
    - The `@context` URL of a matching `@type` is not checked.
  - **Copying the config:** if you copy these configs, copy the `schemas/` mount too, or the adapter will not start.
- **Mock replies.** `install/sandbox-fixtures/` supplies LTS `on_*` replies for the mock CPO, because the replies built into the `fidedocker/sandbox-2.0` image predate LTS.
- **Postman.** Regenerate the collections from the examples with `python3 scripts/generate_postman_collection.py --role BAP|BPP`.

## Related

- [EV charging implementation guide](../../docs/implementation-guides/v2/EV_Charging/EV_Charging.md)
- [Migration kit](../ev-charging-migration-kit/), for apps still on the earlier `message.order` shape
- [Data Exchange Devkit](../data-exchange/)
