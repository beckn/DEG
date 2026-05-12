# BecknReportDescriptors

OpenADR 3.1.0-aligned sidecar schema declaring which telemetry signals a seller commits to reporting under a DEG contract. Embedded as `inputs[seller].inputs.reportDescriptors` in offer attributes (e.g. `DemandFlexBuyOffer`).

**Canonical IRI:** `https://schema.beckn.io/BecknReportDescriptors/v1.0`

**Namespace prefix:** `deg:` → `https://schema.beckn.io/deg/BecknReportDescriptors/v1.0/`

---

## Versions

| Version | Status | Notes |
|---------|--------|-------|
| [v1.0](./v1.0/) | Current | Initial version. Reuses OpenADR3 `reportPayloadDescriptor` and adds a `cardinality` extension. |

---

## Schemas

### `BecknReportDescriptors`

Array of `BecknReportPayloadDescriptor` entries — one per signal the seller commits to reporting.

### `BecknReportPayloadDescriptor`

Extends OpenADR3 `reportPayloadDescriptor` with one DEG field:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `payloadType` | `string` | ✓ | Signal identifier (e.g. `USAGE`, `POWER`, `SOC_END`, `GPS_LAT`). |
| `units` | `string` | ✓ | Unit of measure (e.g. `KW`, `PERCENT`, `DEGREES`). |
| `readingType` | `string` | | OpenADR3 reading type (e.g. `DIRECT_READ`). |
| `cardinality` | `string` enum | | `PER_INTERVAL` (default) — reported every interval; `PER_EVENT` — reported once per event on interval 0. |

---

## Standard payloadType vocabulary

| payloadType | units | cardinality | Meaning |
|-------------|-------|-------------|---------|
| `BASELINE` | `KW` | `PER_INTERVAL` | Reference (vendor-rated) charge power |
| `USAGE` | `KW` | `PER_INTERVAL` | Measured charge power during the event |
| `POWER` | `KW` | `PER_INTERVAL` | Signed instantaneous power (charge +, discharge −) |
| `SOC_END` | `PERCENT` | `PER_INTERVAL` | State of charge at end of each interval |
| `GPS_LAT` | `DEGREES` | `PER_EVENT` | Vehicle latitude at start of event |
| `GPS_LON` | `DEGREES` | `PER_EVENT` | Vehicle longitude at start of event |
