# IES ARR Filing Schemas

Schemas for Aggregate Revenue Requirement (ARR) filings by distribution licensees to State Electricity Regulatory Commissions (SERCs).

**Source:** [`India-Energy-Stack/ies-docs` (arr-schema-specs-rdx)](https://github.com/India-Energy-Stack/ies-docs/tree/arr-schema-specs-rdx/implementation-guides/data_exchange/specs)

**Tags:** `ies` . `arr` . `regulatory` . `tariff` . `discom`

---

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.0 schema definitions for ARR types |
| [context.jsonld](./context.jsonld) | JSON-LD context mapping ARR terms |

---

## Schemas

| Schema | Description |
|--------|-------------|
| `IES_ARR_Filing` | Complete ARR filing — licensee, commission, fiscal years, line items |
| `IES_ARR_FiscalYear` | Single fiscal year with amount basis (AUDITED/APPROVED/PROPOSED) |
| `IES_ARR_LineItem` | Cost, income, subtotal, or adjustment line item |

---

## Filing Types

| Type | Description |
|------|-------------|
| `MYT` | Multi-Year Tariff control period filing (multiple years) |
| `ANNUAL` | Single year or historical year-by-year approved data |
| `TRUE_UP` | Reconciliation of actuals vs previously approved amounts |
| `REVISED` | Amended filing with corrections |

---

## Related

- [IES Core Schemas](../core/) — IES_Report, IES_Program, IES_Policy
- [DDM DatasetItem](https://github.com/beckn/DDM/tree/main/specification/schema/DatasetItem/v1) — Parent schema; ARR filings are carried in `dataPayload`
