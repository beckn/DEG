# ConnectorType

> **Canonical IRI:** [`https://schema.beckn.io/ConnectorType`](https://schema.beckn.io/ConnectorType)
> **Tags:** `ev-charging, connector, enumeration, ocpi, beckn`
> **Namespace:** `https://schema.beckn.io/`
> Part of the [DEG Schema](../../README.md)

---

**EV connector type enumeration** — the single source of truth for physical connector interface identifiers used by DEG EV charging schemas. Referenced by `EvChargingService` and `EvChargingSession` via their `connectorType` property.

## Versions

| Version | attributes.yaml | context.jsonld | vocab.jsonld |
|---------|----------------|----------------|--------------|
| **v2.0** | [attributes.yaml](./v2.0/attributes.yaml) | [context.jsonld](./v2.0/context.jsonld) | [vocab.jsonld](./v2.0/vocab.jsonld) |

## Values (latest: v2.0)

| Value | IRI | Notes |
|-------|-----|-------|
| `CCS2` | `deg:ConnectorTypeCCS2` | IEC 62196 Combo 2. |
| `Type2` | `deg:ConnectorTypeType2` | IEC 62196 Type 2 (Mennekes), AC. |
| `Type1` | `deg:ConnectorTypeType1` | IEC 62196 Type 1 (SAE J1772). |
| `CHAdeMO` | `deg:ConnectorTypeCHAdeMO` | CHAdeMO DC fast charging. |
| `GB_T` | `deg:ConnectorTypeGBT` | GB/T family (AC/DC not distinguished). |
| `GBT_AC` | `deg:ConnectorTypeGBT_AC` | GB/T AC. |
| `GBT_DC` | `deg:ConnectorTypeGBT_DC` | GB/T DC. |
| `AC-001` | `deg:ConnectorTypeAC001` | Bharat AC-001. |
| `DC-001` | `deg:ConnectorTypeDC001` | Bharat DC-001. |
| `15A` | `deg:ConnectorType15A` | 15A current rating (see notes). |
| `IEC_AC` | `deg:ConnectorTypeIECAC` | Generic IEC AC. |
| `IEC_60309` | `deg:ConnectorTypeIEC60309` | IEC 60309 industrial. |
| `Anderson` | `deg:ConnectorTypeAnderson` | Anderson-style DC. |
| `Type6` | `deg:ConnectorTypeType6` | IEC 62196-6 / IS 17017-2-6 (LEV). |

## Linked Data

| Resource | URL |
|----------|-----|
| Canonical IRI | `https://schema.beckn.io/ConnectorType` |
| JSON Schema (latest) | `https://schema.beckn.io/ConnectorType/v2.0` |
| context.jsonld (latest) | `https://schema.beckn.io/ConnectorType/v2.0/context.jsonld` |
| vocab.jsonld (latest) | `https://schema.beckn.io/ConnectorType/v2.0/vocab.jsonld` |
| Root context.jsonld | `https://schema.beckn.io/context.jsonld` |
| Root vocab.jsonld | `https://schema.beckn.io/vocab.jsonld` |
