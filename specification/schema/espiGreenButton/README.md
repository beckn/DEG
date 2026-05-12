# espiGreenButton

> **Canonical IRI:** [`http://naesb.org/espi`](http://naesb.org/espi)
> **Tags:** `energy`, `metering`, `green-button`, `espi`, `naesb`
> **Namespace:** `http://naesb.org/espi#`
> **Source XSD:** [`https://www.naesb.org/espi.xsd`](https://www.naesb.org/espi.xsd)
> Part of the [DEG Specification](../../README.md)

---

JSON-LD context and RDF vocabulary for Green Button / ESPI (Energy Services Provider Interface) types, as defined by NAESB REQ.21 and IEEE 2030.5.

This schema provides the core metering and billing types used by the Meter Data VC and Billing Summary VC energy credentials. All enumeration codes match the ESPI/NAESB numeric codes exactly.

## Files

| File | Description |
|------|-------------|
| [v1.0/attributes.yaml](./v1.0/attributes.yaml) | OpenAPI 3.0 schema definitions for all ESPI types (generated from `espi.xsd`) |
| [v1.0/context.jsonld](./v1.0/context.jsonld) | JSON-LD context mapping ESPI types and properties to `http://naesb.org/espi#` IRIs |
| [v1.0/vocab.jsonld](./v1.0/vocab.jsonld) | RDF vocabulary (RDFS classes and properties) with `skos:exactMatch` links to ESPI XSD types |

## Linked Data

| Resource | URL |
|----------|-----|
| Namespace IRI | `http://naesb.org/espi#` |
| Source XSD | `https://www.naesb.org/espi.xsd` |
| JSON-LD context | `https://schema.beckn.io/espiGreenButton/v1.0/context.jsonld` |
| RDF vocabulary | `https://schema.beckn.io/espiGreenButton/v1.0/vocab.jsonld` |
| Green Button docs | [utilityapi.com/docs/greenbutton/xml](https://utilityapi.com/docs/greenbutton/xml) |

## Types

| Type | ESPI Source | Description |
|------|------------|-------------|
| `IntervalBlock` | `espi:IntervalBlock` | Time sequence container for meter readings |
| `IntervalReading` | `espi:IntervalReading` | Single metered value with time period, cost, and quality |
| `ReadingType` | `espi:ReadingType` | Metadata: commodity, UOM, flow direction, accumulation, phase, etc. |
| `DateTimeInterval` | `espi:DateTimeInterval` | Start timestamp (ISO 8601) + duration in seconds |
| `ServiceCategory` | `espi:ServiceCategory` | Service type: 0=electricity, 1=gas, 2=water, ... |
| `UsageSummary` | `espi:UsageSummary` | Billing period summary with bills, charges, and consumption |
| `SummaryMeasurement` | `espi:SummaryMeasurement` | Aggregated value with UOM and power-of-ten multiplier |
| `ReadingQuality` | `espi:ReadingQuality` | Quality code for a reading (0=valid, 17=validated, ...) |
| `LineItem` | `espi:LineItem` | Charge or credit line item within a billing period |

## Key Enumerations

### ServiceCategory.kind (ServiceKind)

| Code | Description |
|------|-------------|
| 0 | Electricity |
| 1 | Gas |
| 2 | Water |
| 4 | Heat |

### ReadingQuality.quality / qualityOfReading (QualityOfReading)

| Code | Description |
|------|-------------|
| 0 | Valid / verified |
| 7 | Manually edited |
| 8 | Estimated using reference day |
| 9 | Estimated using linear interpolation |
| 10 | Questionable (failed checks) |
| 11 | Derived (calculated) |
| 12 | Projected (forecast) |
| 13 | Mixed quality |
| 14 | Raw (unvalidated) |
| 15 | Normalized for weather |
| 16 | Other |
| 17 | Validated |
| 18 | Verified |
| 19 | Billing approved |

### ReadingType.uom (UnitSymbolKind) — Common Codes

| Code | Symbol | Description |
|------|--------|-------------|
| 5 | A | Ampere (current) |
| 29 | V | Volt (potential) |
| 33 | Hz | Hertz (frequency) |
| 38 | W | Watt (real power) |
| 42 | m3 | Cubic metre (volume) |
| 61 | VA | Volt-Ampere (apparent power) |
| 63 | VAr | Volt-Ampere reactive |
| 72 | Wh | Watt-hour (real energy) |

### ReadingType.commodity (CommodityKind) — Common Codes

| Code | Description |
|------|-------------|
| 0 | Not applicable |
| 1 | Electricity (secondary metered) |
| 2 | Electricity (primary metered) |
| 7 | Natural gas |
| 9 | Potable water |

### ReadingType.flowDirection (FlowDirectionKind)

| Code | Description |
|------|-------------|
| 0 | Not applicable |
| 1 | Forward (delivered to customer) |
| 4 | Net |
| 19 | Reverse (received from customer) |
| 20 | Total |

### ReadingType.accumulationBehaviour (AccumulationBehaviourKind)

| Code | Description |
|------|-------------|
| 0 | Not applicable |
| 1 | Bulk quantity |
| 2 | Continuous cumulative |
| 3 | Cumulative |
| 4 | Delta data (interval difference) |
| 6 | Indicating |
| 9 | Summation |
| 12 | Instantaneous |

### LineItem.itemKind (ItemKind)

| Code | Description |
|------|-------------|
| 1 | Energy generation fee |
| 2 | Energy delivery fee |
| 3 | Energy usage fee |
| 4 | Administrative fee |
| 5 | Tax |
| 6 | Energy generation credit |
| 7 | Energy delivery credit |
| 8 | Administrative credit |
| 9 | Payment |
| 10 | Information |

### ReadingType.currency (Currency) — ISO 4217 Numeric

| Code | Currency |
|------|----------|
| 0 | Other |
| 36 | AUD |
| 124 | CAD |
| 156 | CNY |
| 208 | DKK |
| 356 | INR |
| 392 | JPY |
| 578 | NOK |
| 643 | RUB |
| 752 | SEK |
| 756 | CHF |
| 826 | GBP |
| 840 | USD |
| 978 | EUR |

## Cost Encoding

All monetary values (`cost`, `billLastPeriod`, `costAdditionalLastPeriod`, `amount`, `unitCost`) accept both integer and float:

**Integer mode (ESPI native):** value is in **hundred-thousandths** (1e-5) of the currency unit.

Example: `cost: 281300` with `currency: 840` (USD) → 281300 × 10⁻⁵ = $2.813

**Float mode (exact):** value is the direct currency amount. A decimal point signals this mode.

Example: `cost: 2.813` with `currency: "USD"` → $2.813

> **Note:** JSON has a single `number` type — there is no schema-level way to enforce integer vs float. The distinction is a serialization convention: if the value contains a decimal point, it is treated as exact; otherwise as hundred-thousandths. JSON parsers may normalize `281300.0` to `281300`, so implementations SHOULD prefer integer mode for ESPI compatibility.

## Timestamps

Timestamps use ISO 8601 format with optional timezone offset:
- `"2025-07-14T18:30:00Z"` (UTC)
- `"2025-07-15T00:00:00+05:30"` (Asia/Kolkata)

Duration is always in seconds (integer).
