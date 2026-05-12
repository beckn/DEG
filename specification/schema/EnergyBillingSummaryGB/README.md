# BillingSummary

> **Canonical IRI:** [`https://schema.beckn.io/EnergyBillingSummaryGB`](https://schema.beckn.io/EnergyBillingSummaryGB)
> **Tags:** `energy`, `billing`, `green-button`, `espi`, `deg`
> **Namespace:** `https://schema.beckn.io/deg/`
> Part of the [DEG Specification](../../../README.md)

---

ESPI/Green Button billing summary data for a single meter. Contains ServiceCategory, currency, and an array of UsageSummary entries (each with billingPeriod, billLastPeriod, overallConsumptionLastPeriod, and optional LineItem breakdown).

## Versions

| Version | attributes.yaml | context.jsonld | vocab.jsonld | README |
|---------|----------------|----------------|--------------|--------|
| **v1.0** | [attributes.yaml](./v1.0/attributes.yaml) | [context.jsonld](./v1.0/context.jsonld) | [vocab.jsonld](./v1.0/vocab.jsonld) | [README](./v1.0/README.md) |

## Properties (latest: v1.0)

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `ServiceCategory` | `object` | ✅ | ESPI ServiceCategory with `kind` |
| `timeZone` | `string` | ✅ | IANA time-zone identifier |
| `currency` | `integer` or `string` | ✅ | ISO 4217 numeric currency code (840=USD, 356=INR, etc.) |
| `UsageSummary` | `array` | ✅ | Array of ESPI UsageSummary entries (billing periods) |

## Linked Data

| Resource | URL |
|----------|-----|
| Canonical IRI | `https://schema.beckn.io/EnergyBillingSummaryGB` |
| JSON Schema (latest) | `https://schema.beckn.io/EnergyBillingSummaryGB/v1.0` |
| context.jsonld (latest) | `https://schema.beckn.io/EnergyBillingSummaryGB/v1.0/context.jsonld` |
| vocab.jsonld (latest) | `https://schema.beckn.io/EnergyBillingSummaryGB/v1.0/vocab.jsonld` |
| ESPI context (imported) | `https://schema.beckn.io/espiGreenButton/v1.0/context.jsonld` |
| CustomerProfile (imported) | `https://schema.beckn.io/EnergyCustomerProfile/v1.0/context.jsonld` |
