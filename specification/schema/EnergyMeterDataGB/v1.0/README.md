# MeterDataGB — v1.0

ESPI/Green Button meter reading data for a single meter. Uses ESPI types (IntervalBlock, ReadingType, IntervalReading, ServiceCategory) natively with numeric or string enum codes. Adds `timeZone` (IANA identifier) as a non-ESPI extension for demand-forecasting.

Part of the [DEG Specification](../../../../README.md) · [MeterDataGB](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1 / JSON Schema definition for `MeterDataGB` |
| [context.jsonld](./context.jsonld) | JSON-LD context — imports ESPI context, adds `deg:meterDataGB` and `deg:timeZone` |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary for VC-specific terms (MeterDataCredential, meterDataGB, timeZone) |

## Dependencies

- [`espiGreenButton`](../../espiGreenButton/) — ESPI types (IntervalBlock, ReadingType, etc.)
- [`CustomerProfile`](../../CustomerProfile/) — shared customer identity (customerNumber, meterNumber, meterType, idRef)

## Properties

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `ServiceCategory` | object | ✅ | ESPI ServiceCategory — `kind`: 0=electricity, 1=gas, 2=water |
| `timeZone` | string | ✅ | IANA time-zone (e.g., Asia/Kolkata). Not ESPI — for forecasting |
| `ReadingType` | object | ✅ | ESPI ReadingType: commodity, flowDirection, uom, accumulationBehaviour, intervalLength, currency, kind, phase |
| `qualityOfReading` | integer/string | — | ESPI QualityOfReading (0=valid, 17=validated) |
| `IntervalBlock` | array | ✅ | ESPI IntervalBlock array with interval + IntervalReading[] |
