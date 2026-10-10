# IES (India Energy Stack) Schemas

External schemas from the [India Energy Stack](https://github.com/India-Energy-Stack/ies-docs) project, vendored here for stable `$ref` resolution.

**Source:** [`India-Energy-Stack/ies-docs`](https://github.com/India-Energy-Stack/ies-docs/tree/main/implementation-guides/data_exchange/specs)

---

## Modules

| Module | Description |
|--------|-------------|
| [core/](./core/) | IES Data Exchange schemas — `IES_Report`, `IES_Program`, `IES_Policy` — built on OpenADR 3.1.0 |
| [arr/](./arr/) | ARR Filing schemas — `IES_ARR_Filing`, `IES_ARR_FiscalYear`, `IES_ARR_LineItem` — regulatory filings |

---

## Usage

These schemas are referenced as `dataPayload` types inside DDM's `DatasetItem` when exchanging energy telemetry and tariff data over beckn.

```jsonld
{
  "@context": "https://raw.githubusercontent.com/beckn/DEG/ies-specs/specification/external/schema/ies/core/context.jsonld",
  "@type": "IES_Report",
  ...
}
```
