# openadr/3.1.0

> **Canonical IRI:** [`https://www.openadr.org/`](https://www.openadr.org/)
> **Tags:** `energy`, `demand-response`, `openadr`, `time-series`
> **Upstream:** OpenADR Alliance — OpenADR 3.1.0
> **Mirror source:** [India-Energy-Stack/ies-docs openadr3.yaml](https://github.com/India-Energy-Stack/ies-docs/tree/main/implementation-guides/data_exchange/specs)
> Part of the [DEG Specification](../../../README.md)

---

OpenADR 3.1.0 time-series primitives vendored here so DEG schemas can `$ref`
them via `schema.beckn.io/openadr/3.1.0` without depending on upstream
availability. Only the schema types used by DEG are included; the full OpenADR
REST API paths are omitted.

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 schema definitions for the OpenADR 3.1.0 time-series primitives used by DEG |

## Types

| Type | Description |
|------|-------------|
| `interval` | A temporal window with an integer `id` and a list of `payloads` (valuesMap rows). An optional per-interval `intervalPeriod` overrides the series default. |
| `intervalPeriod` | Temporal bounds — ISO 8601 `start` datetime and `duration` string (e.g. `PT1H`). The `start` value `"0001-01-01T00:00:00Z"` conventionally means "now"; `duration` `"P9999Y"` means infinity. |
| `valuesMap` | A typed payload row: `type` (string) + `values` (array of number, integer, string, boolean, or `point`). |
| `point` | An `(x, y)` float pair used as a 2-D grid coordinate. |
| `eventPayloadDescriptor` | Sidecar metadata for a signal in an event or offer: `objectType: EVENT_PAYLOAD_DESCRIPTOR`, `payloadType`, optional `units` and `currency`. |
| `reportPayloadDescriptor` | Sidecar metadata for a telemetry signal: `objectType: REPORT_PAYLOAD_DESCRIPTOR`, `payloadType`, optional `units`, `readingType`, `accuracy`, `confidence`. |
| `dateTime` | RFC 3339 datetime string (e.g. `2026-04-26T04:30:00Z`). |
| `duration` | ISO 8601 duration string (e.g. `PT1H`, `P1D`). |
| `units` | Free-string unit label (e.g. `KWH`, `KW`, `STRING`). |
| `readingType` | Free-string reading type (e.g. `DIRECT_READ`). |

## Usage from DEG schemas

DEG schemas reference these types via the canonical `schema.beckn.io` URL:

```yaml
intervalPeriod:
  $ref: "https://schema.beckn.io/openadr/3.1.0#/components/schemas/intervalPeriod"
```

`BecknTimeSeries` uses `interval`, `intervalPeriod`, `eventPayloadDescriptor`,
and `reportPayloadDescriptor` to build a portable, OpenADR-aligned time-series
envelope for any domain signal (price, quantity, allocation, status).
