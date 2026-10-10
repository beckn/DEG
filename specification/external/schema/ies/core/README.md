# IES Core Data Exchange Schemas

Schemas for energy data exchange based on [OpenADR 3.1.0](https://www.openadr.org/), extended with IES-specific semantics for the India Energy Stack.

**Source:** [`India-Energy-Stack/ies-docs/implementation-guides/data_exchange/specs/`](https://github.com/India-Energy-Stack/ies-docs/tree/main/implementation-guides/data_exchange/specs)

**Tags:** `ies` . `openadr` . `meter-data` . `tariff` . `telemetry`

---

## Files

| File | Description |
|------|-------------|
| [attributes.yaml](./attributes.yaml) | OpenAPI 3.1.0 schema definitions for IES types |
| [context.jsonld](./context.jsonld) | JSON-LD context mapping IES and OpenADR terms |
| [openadr3.yaml](./openadr3.yaml) | OpenADR 3.1.0 base spec (referenced via `$ref`) |

---

## Schemas

| Schema | Description | Base |
|--------|-------------|------|
| `IES_Report` | Telemetry report — meter readings, usage data | `oadr:report` |
| `IES_Program` | Tariff program metadata | `oadr:program` |
| `IES_Policy` | Energy policy with slabs and surcharges | IES-native |
| `IES_PolicyRequest` | Client-provided policy description | IES-native |
| `EnergySlab` | Consumption-based pricing tier | IES-native |
| `SurchargeTariff` | Time-of-use surcharge/discount | IES-native |
| `IES_Attribute` | Supplemental metadata (tariff structure, ToU) | IES-native |

---

## IES_Report Structure

An `IES_Report` carries telemetry data (e.g., meter readings from an AMISP). Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Report identifier |
| `objectType` | string | Always `REPORT` |
| `eventID` | string | Associated event ID |
| `clientName` | string | VEN/meter client name |
| `reportName` | string | Human-readable report name |
| `payloadDescriptors` | array | Describes payload types, units, reading type |
| `resources` | array | List of resource reports with intervals |
| `resources[].intervals[].payloads` | array | `{ type, values }` — e.g., `{ type: "USAGE", values: [42.5] }` |

---

## Related

- [DDM DatasetItem](https://github.com/beckn/DDM/tree/main/specification/schema/DatasetItem/v1) — Parent schema; IES types are carried in `dataPayload`
- [OpenADR 3.1.0 Spec](https://www.openadr.org/) — Base protocol for demand response
- [India Energy Stack](https://github.com/India-Energy-Stack/ies-docs) — Upstream source
