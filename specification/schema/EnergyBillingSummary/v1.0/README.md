# BillingSummary — v1.0

ESPI/Green Button billing summary data for a single meter. Uses ESPI types (UsageSummary, SummaryMeasurement, LineItem) natively with numeric or string enum codes. Adds `timeZone` as a non-ESPI extension.

Part of the [DEG Specification](../../../../README.md) · [BillingSummary](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1 / JSON Schema definition for `BillingSummary` |
| [context.jsonld](./context.jsonld) | JSON-LD context — imports ESPI context, adds `deg:billingSummary` and `deg:timeZone` |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary for VC-specific terms (BillingSummaryCredential, billingSummary, timeZone) |

## Dependencies

- [`espiGreenButton`](../../../external/schema/espiGreenButton/) — ESPI types (UsageSummary, SummaryMeasurement, LineItem, DateTimeInterval)
- [`CustomerProfile`](../../CustomerProfile/) — shared customer identity

## Properties

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `ServiceCategory` | object | ✅ | ESPI ServiceCategory — `kind`: 0=electricity, 1=gas, 2=water |
| `timeZone` | string | ✅ | IANA time-zone. Not ESPI |
| `currency` | integer/string | ✅ | ISO 4217 numeric code (840=USD, 356=INR) |
| `UsageSummary` | array | ✅ | Array of ESPI UsageSummary: billingPeriod, billLastPeriod, overallConsumptionLastPeriod, costAdditionalDetailLastPeriod |
