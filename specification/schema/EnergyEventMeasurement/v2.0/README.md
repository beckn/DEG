# EnergyEventMeasurement — v2.0

Per-**EnergyResource** (e.g. smart **meter**) M&V row scoped to an **EnergyEvent**.

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 component `EnergyEventMeasurement` |
| [context.jsonld](./context.jsonld) | JSON-LD context |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## Beckn v2 placement (BDR profile)

- **Recommended:** `message.contract.energyEventMeasurements[]` alongside `energyEvents[]`.
- **Relationship:** `resourceId` SHOULD match `DemandFlexPerformance.meters[].meterId` and seller `participatingMeters` entries when the same meter is used.
- **Relationship:** `eventId` MUST match `EnergyEvent.id` (and typically `DemandFlexPerformance.eventId`).
- **schemaContext:** include this type’s `context.jsonld` when the array is present.

## Required properties

`eventId`, `resourceId`, `measurementPhase`, `measurementWindow` (`startDate`, `endDate` UTC).
