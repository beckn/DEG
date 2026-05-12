# MeterDataGB

> **Canonical IRI:** [`https://schema.beckn.io/EnergyMeterDataGB`](https://schema.beckn.io/EnergyMeterDataGB)
> **Tags:** `energy`, `metering`, `green-button`, `espi`, `deg`
> **Namespace:** `https://schema.beckn.io/deg/`
> Part of the [DEG Specification](../../../README.md)

---

ESPI/Green Button meter reading data for a single meter. Contains ServiceCategory, ReadingType, IntervalBlock with IntervalReadings, and qualityOfReading. All ESPI types and enum codes are used natively.

## Versions

| Version | attributes.yaml | context.jsonld | vocab.jsonld | README |
|---------|----------------|----------------|--------------|--------|
| **v1.0** | [attributes.yaml](./v1.0/attributes.yaml) | [context.jsonld](./v1.0/context.jsonld) | [vocab.jsonld](./v1.0/vocab.jsonld) | [README](./v1.0/README.md) |

## Properties (latest: v1.0)

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `ServiceCategory` | `object` | ✅ | ESPI ServiceCategory with `kind` (0=electricity, 1=gas, 2=water) |
| `timeZone` | `string` | ✅ | IANA time-zone identifier (not ESPI — added for forecasting) |
| `ReadingType` | `object` | ✅ | ESPI ReadingType: commodity, flowDirection, uom, accumulationBehaviour, etc. |
| `qualityOfReading` | `integer` or `string` | — | ESPI QualityOfReading (0=valid, 17=validated, etc.) |
| `IntervalBlock` | `array` | ✅ | Array of ESPI IntervalBlocks with IntervalReadings |

## Linked Data

| Resource | URL |
|----------|-----|
| Canonical IRI | `https://schema.beckn.io/EnergyMeterDataGB` |
| JSON Schema (latest) | `https://schema.beckn.io/EnergyMeterDataGB/v1.0` |
| context.jsonld (latest) | `https://schema.beckn.io/EnergyMeterDataGB/v1.0/context.jsonld` |
| vocab.jsonld (latest) | `https://schema.beckn.io/EnergyMeterDataGB/v1.0/vocab.jsonld` |
| ESPI context (imported) | `https://schema.beckn.io/espiGreenButton/v1.0/context.jsonld` |
| CustomerProfile (imported) | `https://schema.beckn.io/EnergyCustomerProfile/v1.0/context.jsonld` |
