# BecknTimeSeries — v1.0

Lightweight, OpenADR 3.1.0-aligned time-series envelope for beckn payloads.

Part of the [DEG Schema](../../) · [BecknTimeSeries](../README.md)

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.1 components.schemas.`BecknTimeSeries` (re-uses OpenADR3 types via `$ref`) |
| [context.jsonld](./context.jsonld) | JSON-LD context — term `TimeSeries` maps to `beckn:TimeSeries` |
| [vocab.jsonld](./vocab.jsonld) | RDF vocabulary |

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `intervalPeriod` | object | ✓ | Default `{start, duration}` (ISO 8601) for the series. |
| `payloadDescriptors` | array | ✓ | `{payloadType, units, currency, readingType, …}` per signal. Every type used in `intervals` MUST appear here. |
| `intervals` | array | ✓ | Series rows; each `{id, [intervalPeriod], payloads[]}`. `payloads[]` is a list of `{type, values[]}` valuesMap rows. |

## `payloadType` is open at this layer

BecknTimeSeries inherits OpenADR's open-string `payloadType` (any
`minLength:1, maxLength:128` string is accepted). Domain profiles that
embed BecknTimeSeries SHOULD close the set to their own vocabulary and
encode "every `intervals[*].payloads[*].type` appears in
`payloadDescriptors`" as a profile-level cross-field check. That keeps
BecknTimeSeries domain-neutral and pushes opinionation into the consumer
schema. DEG sign convention follows OpenADR: encode direction in the
type name (`USAGE` vs `INJECTION`, `UP_REGULATION_CAPACITY` vs
`DOWN_REGULATION_CAPACITY`), keep magnitudes positive, and reserve
signed values for explicit `DELTA_*` types.

## Two ways to embed in a parent payload

**(a) Inline via `$ref` — preferred for typed properties.** Parent schema
points at `BecknTimeSeries#/components/schemas/BecknTimeSeries`. Embedded
payload only needs the body — `@context` is declared once in the
envelope's `context.schemaContext[]`. `@type` is optional but useful for
human readers.

```yaml
# In the parent attributes.yaml
telemetry:
  $ref: "https://schema.beckn.io/BecknTimeSeries/v1.0#/components/schemas/BecknTimeSeries"
```

**(b) Discovery via `@context` — for polymorphic carriers.** Parent
schema declares only the JSON-LD envelope; the embedded payload carries
its own `@context`+`@type`, and beckn-onix's extended-schema validator
discovers and routes it. Use this when the carrier may hold *one of
several* schemas (e.g. `contractTerms` could be a DEGContract or some
other contract type).

## Minimal example — single-signal, two intervals (inline-`$ref` mode)

```json
{
  "@type": "TimeSeries",
  "intervalPeriod": { "start": "2026-04-01T08:30:00Z", "duration": "PT1H" },
  "payloadDescriptors": [
    { "objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "BASELINE", "units": "KW", "readingType": "DIRECT_READ" }
  ],
  "intervals": [
    { "id": 0, "payloads": [ {"type": "BASELINE", "values": [45.0]} ] },
    { "id": 1, "payloads": [ {"type": "BASELINE", "values": [44.0]} ] }
  ]
}
```

## Multi-signal example — scalar + 2-D point in the same interval

```json
{
  "@type": "TimeSeries",
  "intervalPeriod": { "start": "2026-04-01T08:30:00Z", "duration": "PT15M" },
  "payloadDescriptors": [
    { "objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "PRICE",         "units": "INR_PER_KWH", "currency": "INR" },
    { "objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "FORECAST_BAND", "units": "KW" }
  ],
  "intervals": [
    {
      "id": 0,
      "payloads": [
        { "type": "PRICE",         "values": [12] },
        { "type": "FORECAST_BAND", "values": [ {"x": 10, "y": 14} ] }
      ]
    }
  ]
}
```

## What the schema validator catches vs. what it doesn't

`BecknTimeSeries` reuses OpenADR3 shapes via `$ref`. The beckn-onix /
kin-openapi validator will flag:

- wrong types, missing `payloads` / `values`
- missing `payloadDescriptors`, `intervals` shorter than `minItems: 1`
- malformed ISO datetime / ISO duration
- value elements that are neither number / string / boolean / `point`

It does **not** catch (these belong in consumer profiles or the policy
layer):

- `payloadType` / `type` membership in a domain-specific set — close the
  enum in the consumer profile and encode it in 2020-12 `if/then/else`
  (silent under kin-openapi < v0.136.0; enforced once
  [PR #1125](https://github.com/getkin/kin-openapi/pull/1125) lands)
- cross-field membership ("every type used in `intervals` is declared in
  `payloadDescriptors`") — same vehicle as above, or run it in Rego;
  see [`specification/policies/demand_flex_revenue.rego`](../../../policies/demand_flex_revenue.rego)
- value-conditioned cardinality (e.g. "PRICE rows must have exactly one
  number, FORECAST_BAND must have exactly one point")
- cross-row alignment ("every interval carries the same set of `type`
  keys")

## Why this lives in DEG

OpenADR's `report.resources[].intervals[]` is the most battle-tested
shape for interval-aligned energy data. Published at `schema.beckn.io/openadr/3.1.0` (source in
[`specification/schema/openadr/v3.1.0/`](../../openadr/v3.1.0/))
and `$ref`-imported via that URL, giving DEG schemas a uniform time-series idiom
without copying types. Each domain schema (e.g. `DemandFlexPerformance`)
embeds `BecknTimeSeries` under whatever attribute carries series data
— typically `telemetry`.
