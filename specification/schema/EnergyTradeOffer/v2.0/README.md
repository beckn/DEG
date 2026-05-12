# EnergyTradeOffer — v2.0

Offer attributes for P2P energy trading. Attached to `Offer.offerAttributes`.

Part of the [DEG Schema](../../../specification/schema/) · [EnergyTradeOffer](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 schema for `EnergyTradeOffer` |
| [context.jsonld](./context.jsonld) | JSON-LD context (namespace: `https://schema.beckn.io/deg/EnergyTradeOffer/v2.0/`) |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary for `EnergyTradeOffer` terms |

## Design: single commitmentAttributes timeseries

All interval data (price, quantities, allocations) lives in a single
`Commitment.commitmentAttributes` BecknTimeSeries that grows as the contract
progresses:

| Lifecycle stage | Role adds to commitmentAttributes |
|-----------------|-----------------------------------|
| publish / on_select | seller: `PRICE_PER_KWH`, `AVAILABLE_QTY` |
| init / confirm | buyer: `REQUESTED_QTY` (same intervals) |
| post-delivery | discoms: `BUYER_DISCOM_ALLOC`, `BUYER_DISCOM_STATUS`, `SELLER_DISCOM_ALLOC`, `SELLER_DISCOM_STATUS`, `FINAL_ALLOC` |

A developer touches one BecknTimeSeries block instead of three separate named
timeseries objects, and the full trade history is visible in one place.

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `validityWindow` | `TimePeriod` | | Window during which the offer can be selected/accepted |
| `inputs` | `RoleInputs[]` | | One entry per role; declares payloadDescriptors for each role |
| `contractTerms` | `object` (JSON-LD) | | DEGContract terms at catalog publish time; MUST carry `@context` and `@type` |

## RoleInputs

Each `inputs[*]` entry has:

| Field | Type | Description |
|-------|------|-------------|
| `role` | `seller` \| `buyer` \| `buyerDiscom` \| `sellerDiscom` | Role identifier |
| `participantId` | `string \| null` | Bound at init/confirm; null at catalog for buyer/discom |
| `payloadDescriptors` | `eventPayloadDescriptor[] \| reportPayloadDescriptor[]` | Signal types this role contributes |

Required payloadDescriptors per role:

| Role | Required descriptors |
|------|----------------------|
| `seller` | `PRICE_PER_KWH` (currency: INR), `AVAILABLE_QTY` (units: KWH) |
| `buyer` | `REQUESTED_QTY` (units: KWH) |
| `buyerDiscom` | `BUYER_DISCOM_ALLOC` (units: KWH), `BUYER_DISCOM_STATUS` (units: STRING) |
| `sellerDiscom` | `SELLER_DISCOM_ALLOC` (units: KWH), `SELLER_DISCOM_STATUS` (units: STRING) |

## Commitment.commitmentAttributes (BecknTimeSeries)

`commitmentAttributes` on the `Commitment` object (per Beckn v2.0 LTS spec) carries
a `BecknTimeSeries` (`@type: "TimeSeries"`) that is the authoritative record of all
slot-level values for the trade.

Consistency requirement: every `payloadType` in
`commitmentAttributes.intervals[*].payloads[*].type` MUST appear in
`commitmentAttributes.payloadDescriptors`, and vice versa.
