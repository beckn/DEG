# EnergyEvent — v2.0

Identifies a **single BDR/flex event** (scheduling + lifecycle) and links it to the Beckn **contract**, **commitment**, and catalog **flex need** resource.

Part of demand-flexibility / BDR schema set alongside `DemandFlexNeed`, `DemandFlexPerformance`, `EnergyEventParticipation`.

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 component `EnergyEvent` |
| [context.jsonld](./context.jsonld) | JSON-LD context |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## Beckn v2 placement (BDR profile)

- **Recommended:** `message.contract.energyEvents` — array of `EnergyEvent` objects (extended contract payload; include this type in `schemaContext`).
- **Cross-reference:** set `DemandFlexPerformance.eventId` to `EnergyEvent.id` for M&V rows tied to this occurrence.
- **Utility (BPP):** create/update events when announcing or changing the dispatch window; set `status` through the lifecycle.

## Required properties

`id`, `status`, `eventWindow` (`startDate`, `endDate` in UTC).
