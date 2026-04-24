# Billing Summary Credential

A credential for aggregated billing period data with costs and consumption totals, aligned with Green Button (ESPI/NAESB) UsageSummary semantics.

## Purpose

This credential captures monthly billing summaries for a single meter. It is:
- **Issued by** the distribution utility
- **Held by** the customer (prosumer/consumer)
- **Presented to** credit-check services, program eligibility platforms, or energy analytics providers

Key use cases:
- Creditworthiness assessment for energy programs
- Historical spend analysis across utility boundaries
- Program eligibility verification based on consumption patterns
- Energy cost benchmarking

## Relationship to Meter Data Credential

The Billing Summary Credential and Meter Data Credential are complementary but serve different purposes:

| Aspect | Meter Data VC | Billing Summary VC |
|--------|--------------|-------------------|
| Granularity | 15-minute intervals | Monthly billing periods |
| Primary data | Energy consumption (kWh) | Cost ($) + consumption |
| Typical size | Thousands of readings | 12–24 billing periods |
| Audience | Forecasting, P2P trading | Credit checks, eligibility |
| ESPI source | IntervalBlock + IntervalReading | UsageSummary + billing IntervalReading |

Both credentials link to the same customer via DID, customerProfile.customerNumber, and customerProfile.meterNumber.

## Fields

### credentialSubject

| Field | Type | Required | Description | Green Button Source |
|-------|------|----------|-------------|---------------------|
| `id` | string (DID) | Yes | Customer DID | — |
| `customerProfile.customerNumber` | string | Yes | Utility account number | — |
| `customerProfile.meterNumber` | string | Yes | Meter serial number | — |
| `customerProfile.meterType` | string | Yes | Meter type (Smart, Conventional, etc.) | — |
| `billingSummary.serviceKind` | enum | Yes | electricity / gas / water | `UsagePoint.ServiceKind` |
| `billingSummary.timeZone` | string | Yes | IANA time-zone | — |
| `billingSummary.currency` | string | Yes | ISO 4217 currency code | `UsageSummary.currency` |
| `billingSummary.coveragePeriod` | object | Yes | Summary date range | — |
| `billingSummary.billingPeriods` | array | Yes | Array of billing period summaries | `UsageSummary` |

### billingPeriods[]

| Field | Type | Required | Description | ESPI Element |
|-------|------|----------|-------------|--------------|
| `period.start` | datetime | Yes | Start of billing period (ISO 8601) | `billingPeriod.start` |
| `period.duration` | integer | Yes | Duration in seconds | `billingPeriod.duration` |
| `billAmount` | number | Yes | Total bill amount. Integer mode: thousandths of currency unit. Decimal mode: direct currency amount | `billLastPeriod` |
| `consumption.value` | number | Yes | Total consumption value | `overallConsumptionLastPeriod.value` |
| `consumption.uom` | enum | Yes | Unit of measure (Wh, kWh, etc.) | `overallConsumptionLastPeriod.uom` |
| `consumption.powerOfTenMultiplier` | integer | No | Scale factor; defaults to 0 | `overallConsumptionLastPeriod.powerOfTenMultiplier` |
| `additionalCosts` | number | No | Surcharges, fees, etc. Same encoding as billAmount | `costAdditionalLastPeriod` |
| `qualityOfReading` | enum | No | Data quality for this period | `qualityOfReading` |
| `lineItems` | array | No | Itemised breakdown of charges and credits | `costAdditionalDetailLastPeriod` |

### lineItems[]

| Field | Type | Required | Description | ESPI Element |
|-------|------|----------|-------------|--------------|
| `itemKind` | enum | Yes | Classification of charge/credit | `ItemKind` |
| `amount` | number | Yes | Amount (negative = credit). Same encoding as billAmount | `LineItem.amount` |
| `note` | string | No | Human-readable description | `LineItem.note` |
| `unitCost` | number | No | Per-unit cost (e.g., price per kWh) | `LineItem.unitCost` |
| `itemPeriod.start` | datetime | No | Start of item period (ISO 8601) | `LineItem.itemPeriod.start` |
| `itemPeriod.duration` | integer | No | Duration in seconds | `LineItem.itemPeriod.duration` |

### itemKind enum values

| Value | ESPI Code | Description | Example Use |
|-------|-----------|-------------|-------------|
| `energyGenerationFee` | 1 | Energy generation charge | Generation cost component |
| `energyDeliveryFee` | 2 | Transmission and distribution | Grid delivery charges |
| `energyUsageFee` | 3 | Consumption / demand charges | Peak demand surcharge |
| `administrativeFee` | 4 | Administrative fees | **Late payment penalties**, account fees |
| `tax` | 5 | Taxes | State, local, federal taxes |
| `energyGenerationCredit` | 6 | Generation credit/rebate | **P2P trade credits**, net metering export credits |
| `energyDeliveryCredit` | 7 | Delivery credit/rebate | Grid service rebates |
| `administrativeCredit` | 8 | Admin credit/rebate | Loyalty discounts, billing adjustments |
| `payment` | 9 | Payment for previous balance | Payment received |
| `information` | 10 | Informational (no charge) | Settlement period notice |

## Interpreting Values

### Monetary Fields (billLastPeriod, costAdditionalLastPeriod, amount, unitCost)

All monetary fields accept both integer and float values. JSON has a single `number` type — there is no schema-level way to distinguish `1422300000` from `1422300000.0`. The interpretation is a **convention** determined by whether the serialized value contains a decimal point:

**Integer mode (ESPI/Green Button native):** value is in hundred-thousandths (1e-5) of the currency unit.

**Example:** `billLastPeriod: 1422300000`, `currency: "INR"` → 1422300000 × 10⁻⁵ = ₹14,223.00

**Float mode (exact):** value is the direct currency amount. A decimal point signals this mode.

**Example:** `billLastPeriod: 14223.00`, `currency: "INR"` → ₹14,223.00

> **Note:** JSON parsers may normalize `14223.0` to `14223`, losing the decimal point. Implementations SHOULD use integer mode for ESPI compatibility and only use float mode when the source system provides exact currency amounts. When in doubt, treat a whole number as integer mode (hundred-thousandths).

### Consumption

**Integer mode:** `physical_value = value × 10^powerOfTenMultiplier [in units of uom]`

**Example:** `value: 326979`, `powerOfTenMultiplier: 3`, `uom: "Wh"` → 326,979 × 1000 Wh = 326,979 kWh

**Decimal mode:** `value` is the physical quantity directly in the given UOM.

## Green Button Alignment

| JSON Property | Green Button Source | ESPI Element |
|---|---|---|
| `serviceKind` | UsagePoint.ServiceKind | `espi:ServiceKind` |
| `currency` | UsageSummary.currency | `espi:currency` |
| `billingPeriods` | UsageSummary (repeating) | `espi:UsageSummary` |
| `period` | UsageSummary.billingPeriod | `espi:billingPeriod` |
| `billAmount` | UsageSummary.billLastPeriod | `espi:billLastPeriod` |
| `consumption` | UsageSummary.overallConsumptionLastPeriod | `espi:SummaryMeasurement` |
| `additionalCosts` | UsageSummary.costAdditionalLastPeriod | `espi:costAdditionalLastPeriod` |
| `qualityOfReading` | UsageSummary.qualityOfReading | `espi:QualityOfReading` |
| `lineItems` | UsageSummary.costAdditionalDetailLastPeriod | `espi:LineItem` |
| `itemKind` | LineItem.itemKind | `espi:ItemKind` |
| `amount` | LineItem.amount | `espi:amount` |
| `note` | LineItem.note | `espi:note` |
| `unitCost` | LineItem.unitCost | `espi:unitCost` |
| `itemPeriod` | LineItem.itemPeriod | `espi:itemPeriod` |

## Credential Linkage

This credential links to the Customer Credential via the `credentialSubject.id` (customer DID), `customerProfile.customerNumber`, and `customerProfile.meterNumber` fields. A customer may have multiple Billing Summary Credentials covering different time periods or meters.

## Version

This is **v1.0** of the Billing Summary Credential schema.

## Files

- `attributes.yaml` - OpenAPI 3.1.1 document (JSON Schema 2020-12 dialect) — canonical schema for validation and Swagger rendering
- `context.jsonld` - JSON-LD context for semantic interoperability
- `vocab.jsonld` - RDF vocabulary definitions
- `examples/example.json` - Sample credential with 6 monthly billing periods from real PG&E data structure
- `readme.md` - This documentation

Validate examples against the schema:

```bash
python3 scripts/validate_vc_examples.py specification/schema/EnergyBillingSummaryCredential/v1.0/attributes.yaml
```

The script bundles `attributes.yaml` with `@redocly/cli` (dereferencing cross-schema `$ref`s) and validates each example with `jsonschema` (Draft 2020-12).

## Usage

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://schema.org/",
    "https://schema.beckn.io/EnergyBillingSummary/v1.0/context.jsonld"
  ],
  "type": ["VerifiableCredential", "EnergyBillingSummaryCredential"],
  "issuer": {
    "id": "did:web:pge.com",
    "type": "idRef",
    "name": "Pacific Gas and Electric Company",
    "issuedBy": "did:web:pge.com",
    "subjectId": "CPUC-U-39-E"
  },
  "credentialSubject": {
    "id": "did:example:consumer:pge-5230743477",
    "customerProfile": {
      "customerNumber": "5230743477",
      "meterNumber": "PGE-MTR-001",
      "meterType": "Smart"
    },
    "billingSummary": {
      "serviceKind": "electricity",
      "timeZone": "America/Los_Angeles",
      "currency": "USD",
      "coveragePeriod": {
        "start": "2025-07-01T07:00:00Z",
        "end": "2025-12-31T08:00:00Z"
      },
      "billingPeriods": [
        {
          "period": { "start": "2025-07-01T07:00:00Z", "duration": 2592000 },
          "billAmount": 14223000,
          "consumption": { "value": 326979, "uom": "Wh", "powerOfTenMultiplier": 3 },
          "qualityOfReading": "valid"
        }
      ]
    }
  }
}
```
