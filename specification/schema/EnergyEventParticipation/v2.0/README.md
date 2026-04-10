# EnergyEventParticipation — v2.0

**Per-event** participation for the seller (aggregator): explicit **opt-in** / **opt-out**, program **defaults** tied to buyer `optOutDefault`, and optional **meter** subset.

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 component `EnergyEventParticipation` |
| [context.jsonld](./context.jsonld) | JSON-LD context |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## Beckn v2 placement (BDR profile)

- **Recommended:** `message.contract.energyEventParticipations` — array parallel to `energyEvents`, keyed by `eventId` + `participantId`.
- **Interaction with /update:** BAP may send participation rows or continue to update `participatingMeters` on the offer; implementations SHOULD reconcile into `EnergyEventParticipation` for a clear audit trail.
- **schemaContext:** include this type’s `context.jsonld` whenever the array is present.

## Required properties

`eventId`, `participantId`, `participationStatus`.

## ParticipationStatus semantics

| Value | Meaning |
|:------|:--------|
| `PENDING` | No explicit decision for this event. |
| `OPTED_IN` | Explicitly participating; use `meterIds` when known. |
| `OPTED_OUT` | Explicitly not participating; optional `reason`. |
| `DEFAULT_IN` | Participating by default (`optOutDefault` false on buyer terms) until overridden. |
| `DEFAULT_OUT` | Not participating until explicit opt-in (`optOutDefault` true). |
