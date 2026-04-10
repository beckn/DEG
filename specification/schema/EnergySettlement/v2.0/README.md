# EnergySettlement — v2.0

**Settlement calculation** snapshot: policy reference, **revenue flows**, optional **line items** (per meter / premium / penalty), lifecycle **status**, and **net-zero** flag.

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 — `EnergySettlement`, `SettlementRevenueFlow`, `SettlementLineItem` |
| [context.jsonld](./context.jsonld) | JSON-LD context |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## Beckn v2 placement (BDR profile)

- **Recommended:** `message.contract.energySettlements[]` (array to allow re-runs and corrections).
- **Alignment:** `revenueFlows[]` SHOULD mirror `DEGContract.revenueFlows` when both represent the same policy evaluation.
- **Alignment:** `lineItems[].resourceId` MAY reference the same ids as `EnergyEventMeasurement.resourceId`.
- **schemaContext:** include this type’s `context.jsonld` when the array is present.

## Required properties

`settlementId`, `contractId`, `status`, `computedAt`.
