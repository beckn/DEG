# OpenADR 3.1.0 — Time-Series Primitives

External dependency schema for OpenADR 3.1.0 types used by DEG schemas.

Part of the [DEG Schema](../../) · [openadr](./README.md)

## Files

| Version | Description |
|---------|-------------|
| [v3.1.0/](./v3.1.0/) | OpenAPI 3.1.1 wrappers for OpenADR interval, intervalPeriod, valuesMap, eventPayloadDescriptor, and reportPayloadDescriptor primitives |

## Types

| Type | Description |
|------|-------------|
| `interval` | Temporal window with an integer id and typed payloads |
| `intervalPeriod` | Start timestamp + ISO 8601 duration; sets the default bounds for an interval series |
| `valuesMap` | A typed payload row (`type` + `values` array) |
| `point` | (x, y) float pair |
| `eventPayloadDescriptor` | Sidecar metadata for offer/bid signal types (objectType: `EVENT_PAYLOAD_DESCRIPTOR`) |
| `reportPayloadDescriptor` | Sidecar metadata for telemetry signal types (objectType: `REPORT_PAYLOAD_DESCRIPTOR`) |
| `dateTime` | RFC 3339 datetime string |
| `duration` | ISO 8601 duration string |
| `units` | Unit of measure label (e.g. `KWH`, `KW`, `STRING`) |
| `readingType` | Reading type qualifier (e.g. `DIRECT_READ`) |

## Upstream

OpenADR 3.1.0 specification published by the OpenADR Alliance: https://www.openadr.org/

License: Apache 2.0
