# Meter Data Credential

A credential for historical time-series meter readings, enabling tamper-evident custody of interval data aligned with Green Button (ESPI/NAESB) semantics.

## Purpose

This credential captures historical interval meter readings for a single meter. It is:
- **Issued by** the distribution utility that owns the metering infrastructure
- **Held by** the customer (prosumer/consumer)
- **Presented to** trading apps, demand-response platforms, or forecasting services

Key use cases:
- Single-meter demand forecasting for P2P trading
- Verifiable consumption history for energy programs
- Portable meter data across utility boundaries

## Fields

### credentialSubject

| Field | Type | Required | Description | Green Button Source |
|-------|------|----------|-------------|---------------------|
| `id` | string (DID) | Yes | Customer DID (links to customer) | — |
| `customerProfile.customerNumber` | string | Yes | Utility account number (links to customer record) | — |
| `customerProfile.meterNumber` | string | Yes | Meter serial number | — |
| `customerProfile.meterType` | string | Yes | Meter type (Smart, Conventional, etc.) | — |
| `meterDataGB.serviceKind` | enum | Yes | electricity / gas / water | `UsagePoint.ServiceKind` |
| `meterDataGB.timeZone` | string | Yes | IANA time-zone (e.g., "Asia/Kolkata") | — |
| `meterDataGB.readingType` | object | Yes | What is being measured | `MeterReading.ReadingType` |
| `meterDataGB.qualityOfReading` | enum | No | Overall quality of readings in this credential | `UsageSummary.qualityOfReading` |
| `meterDataGB.coveragePeriod` | object | Yes | Summary date range of data | — |
| `meterDataGB.intervalBlocks` | array | Yes | Blocks of interval readings | `IntervalBlock` |

### readingType

| Field | Type | Required | Description | ESPI Element |
|-------|------|----------|-------------|--------------|
| `commodity` | enum | Yes | Commodity being metered | `CommodityKind` |
| `flowDirection` | enum | Yes | forward / reverse / net | `FlowDirectionKind` |
| `uom` | enum | Yes | Unit of measure (Wh, kWh, W, kW, ...) | `UnitOfMeasure` |
| `powerOfTenMultiplier` | integer | No | Scale factor (0 = ×1, 3 = ×1000); defaults to 0 | `UnitMultiplierKind` |
| `accumulationBehaviour` | enum | Yes | How values accumulate (deltaData, cumulative, ...) | `AccumulationBehaviourKind` |
| `intervalLength` | integer | Yes | Interval length in seconds (e.g., 900 = 15 min) | `intervalLength` |
| `currency` | string | No | ISO 4217 currency code (e.g., "USD", "INR"). Required when cost data is present | `currency` |
| `measurementKind` | enum | No | What is measured: energy, demand, power, voltage, etc. | `MeasurementKind` |
| `phase` | enum | No | Electrical phase: notApplicable, phaseAN, phaseBN, etc. | `PhaseCodeKind` |

### intervalBlocks[].intervalReadings[]

| Field | Type | Required | Description | ESPI Element |
|-------|------|----------|-------------|--------------|
| `timePeriod.start` | datetime | Yes | Start of reading interval (ISO 8601) | `DateTimeInterval.start` |
| `timePeriod.duration` | integer | Yes | Duration in seconds | `DateTimeInterval.duration` |
| `value` | number | Yes | Reading value — integer (scaled by powerOfTenMultiplier + uom) or decimal (direct physical quantity) | `IntervalReading.value` |
| `cost` | number | No | Cost for this interval. Integer = hundred-thousandths (1e-5) of currency. Float = exact cost in currency unit | `IntervalReading.cost` |
| `readingQuality` | enum | No | Quality of this specific reading; overrides credential-level qualityOfReading | `ReadingQuality` |

### qualityOfReading / readingQuality enum values

These map to ESPI `QualityOfReading`:

| Value | ESPI Code | Description |
|-------|-----------|-------------|
| `valid` | 0 | Reading has passed all validation checks |
| `manuallyEdited` | 7 | A human corrected the value |
| `estimatedUsingReferenceDay` | 8 | Estimated from a similar reference day |
| `estimatedUsingLinearInterpolation` | 9 | Gap-filled via interpolation |
| `questionable` | 10 | Failed validation but not yet corrected |
| `derived` | 11 | Calculated from other readings |
| `projected` | 12 | Forecast/projected value |
| `mixed` | 13 | Contains both validated and estimated readings |
| `raw` | 14 | Unvalidated meter data |
| `normalizedForWeather` | 15 | Adjusted for weather conditions |
| `other` | 16 | None of the above |
| `validated` | 17 | Passed automated validation |
| `verified` | 18 | Passed manual verification |

## Interpreting Values

The `value` field may be an integer or a decimal number.

**Integer mode (Green Button compatible):** multiply by the scale factor to get the physical quantity:

```
physical_value = value × 10^powerOfTenMultiplier  [in units of uom]
```

**Example:** `value: 375`, `powerOfTenMultiplier: 0`, `uom: "Wh"` → 375 Wh consumed in that interval.

**Decimal mode (direct):** when `value` is a decimal, `powerOfTenMultiplier` SHOULD be `0` (or omitted) and the value represents the physical quantity directly:

**Example:** `value: 37.5`, `uom: "Wh"` → 37.5 Wh consumed in that interval.

> **Canonicalization:** When using decimal values in signed credentials, implementations MUST use JCS ([RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)) or equivalent canonical serialization before signing to ensure deterministic representation.

## Interpreting Cost

The `cost` field accepts both integer and float values. JSON has a single `number` type — there is no schema-level way to distinguish `281300` from `281300.0`. The interpretation is a **convention** determined by whether the serialized value contains a decimal point:

**Integer mode (ESPI/Green Button native):** cost is in hundred-thousandths (1e-5) of the currency unit:

**Example:** `cost: 281300`, `currency: "INR"` → 281300 × 10⁻⁵ = ₹2.813 for that interval.

**Float mode (exact):** cost is the direct currency amount. A decimal point signals this mode:

**Example:** `cost: 2.813`, `currency: "INR"` → ₹2.813 for that interval.

> **Note:** JSON parsers may normalize `281300.0` to `281300`, losing the decimal point. Implementations SHOULD use integer mode for ESPI compatibility and only use float mode when the source system provides exact currency amounts. When in doubt, treat a whole number as integer mode (hundred-thousandths).

## Green Button Alignment

This credential uses Green Button / ESPI numeric enum codes directly. The full ESPI schema and enum reference is at `external/schema/espiGreenButton/attributes.yaml`. See `external/schema/espiGreenButton/README.md` for the enum lookup tables.

| JSON Property | Green Button Source | ESPI Element |
|---|---|---|
| `serviceKind` | UsagePoint.ServiceKind | `espi:ServiceKind` |
| `readingType` | MeterReading.ReadingType | `espi:ReadingType` |
| `commodity` | ReadingType.commodity | `espi:CommodityKind` |
| `flowDirection` | ReadingType.flowDirection | `espi:FlowDirectionKind` |
| `uom` | ReadingType.uom | `espi:UnitOfMeasure` |
| `powerOfTenMultiplier` | ReadingType.powerOfTenMultiplier | `espi:UnitMultiplierKind` |
| `accumulationBehaviour` | ReadingType.accumulationBehaviour | `espi:AccumulationBehaviourKind` |
| `intervalLength` | ReadingType.intervalLength | `espi:intervalLength` |
| `currency` | ReadingType.currency | `espi:currency` |
| `measurementKind` | ReadingType.kind | `espi:MeasurementKind` |
| `phase` | ReadingType.phase | `espi:PhaseCodeKind` |
| `qualityOfReading` | UsageSummary.qualityOfReading | `espi:QualityOfReading` |
| `intervalBlocks` | IntervalBlock | `espi:IntervalBlock` |
| `intervalReadings` | IntervalReading | `espi:IntervalReading` |
| `timePeriod` | IntervalReading.timePeriod | `espi:DateTimeInterval` |
| `value` | IntervalReading.value | `espi:value` |
| `cost` | IntervalReading.cost | `espi:cost` |
| `readingQuality` | IntervalReading.ReadingQuality | `espi:ReadingQuality` |

## Credential Linkage

This credential links to the Customer Credential via the `credentialSubject.id` (customer DID), `customerProfile.customerNumber` (utility account number), and `customerProfile.meterNumber` fields. A customer may have multiple Meter Data Credentials covering different time periods or meters.

## Version

This is **v1.0** of the Meter Data Credential schema.

## Files

- `attributes.yaml` - OpenAPI 3.1.1 document (JSON Schema 2020-12 dialect) — canonical schema for validation and Swagger rendering
- `context.jsonld` - JSON-LD context for semantic interoperability
- `vocab.jsonld` - RDF vocabulary definitions
- `examples/example.json` - Sample credential with 15-minute residential data using integer values and cost (single VC, pretty-printed)
- `examples/example-decimal.json` - Sample credential using decimal values with per-reading quality override
- `examples/example.ndjson` - Sample NDJSON stream with 3 consecutive daily VCs for bulk transport
- `ndjson-transport.md` - NDJSON bulk delivery transport specification
- `readme.md` - This documentation

Validate examples against the schema:

```bash
python3 scripts/validate_vc_examples.py specification/schema/EnergyMeterDataCredential/v1.0/attributes.yaml
```

The script bundles `attributes.yaml` with `@redocly/cli` (dereferencing cross-schema `$ref`s) and validates each example with `jsonschema` (Draft 2020-12).

## Usage

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://schema.org/",
    "https://schema.beckn.io/EnergyMeterDataGB/v1.0/context.jsonld"
  ],
  "type": ["VerifiableCredential", "EnergyMeterDataCredential"],
  "issuer": {
    "id": "did:web:example-utility.com",
    "type": "idRef",
    "name": "Example Energy Utility",
    "issuedBy": "did:web:example-utility.com",
    "subjectId": "REG-2025-00001"
  },
  "credentialSubject": {
    "id": "did:example:consumer:abc123",
    "customerProfile": {
      "customerNumber": "UTIL-2025-001234567",
      "meterNumber": "MET2025789456123",
      "meterType": "Smart"
    },
    "meterDataGB": {
      "serviceKind": "electricity",
      "timeZone": "Asia/Kolkata",
      "readingType": {
        "commodity": "electricitySecondaryMetered",
        "flowDirection": "forward",
        "uom": "Wh",
        "powerOfTenMultiplier": 0,
        "accumulationBehaviour": "deltaData",
        "intervalLength": 900,
        "currency": "INR",
        "measurementKind": "energy"
      },
      "qualityOfReading": "validated",
      "coveragePeriod": {
        "start": "2025-07-14T18:30:00Z",
        "end": "2025-07-14T19:30:00Z"
      },
      "intervalBlocks": [ ... ]
    }
  }
}
```
