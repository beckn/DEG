# EvChargingSession

> **Canonical IRI:** [`https://schema.nfh.global/EvChargingSession`](https://schema.nfh.global/EvChargingSession)
> **Tags:** `ev-charging, session, fulfillment, telemetry, billing, reservation, ocpp, energy, beckn`
> **Namespace:** `https://schema.nfh.global/`
> Part of the [DEG Schema](../../README.md)

---

**EV charging session attributes** attached to `Order.fulfillments[].attributes` in a Beckn EV-charging transaction. Captures real-time or completed charging session data — including session status, energy consumed, duration, total cost, telemetry intervals, and tracking links.

## Versions

| Version | attributes.yaml | context.jsonld | vocab.jsonld | README |
|---------|----------------|----------------|--------------|--------|
| **v1.0** | [attributes.yaml](./v1.0/attributes.yaml) | [context.jsonld](./v1.0/context.jsonld) | [vocab.jsonld](./v1.0/vocab.jsonld) | [README](./v1.0/README.md) |
| **v2.0** | [attributes.yaml](./v2.0/attributes.yaml) | [context.jsonld](./v2.0/context.jsonld) | [vocab.jsonld](./v2.0/vocab.jsonld) | [README](./v2.0/README.md) |
| **v3.0** | [attributes.yaml](./v3.0/attributes.yaml) | [context.jsonld](./v3.0/context.jsonld) | [vocab.jsonld](./v3.0/vocab.jsonld) | [README](./v3.0/README.md) |

v3.0 is the settlement-first redesign used by [devkits/ev-charging/uc2-ev-charging](../../../devkits/ev-charging/uc2-ev-charging/); see its [README](./v3.0/README.md). The table below describes v2.0.

## Properties (v2.0)

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `sessionStatus` | `string` (enum) | — | High-level session state: `PENDING`, `ACTIVE`, `STOP`, `COMPLETED`, `INTERRUPTED`. |
| `connectorStatus` | `string` (enum) | — | Charging connector status (OCPP codes): `AVAILABLE`, `PREPARING`, `UNAVAILABLE`. |
| `buyerFinderFee` | `object` | — | Commission payable by provider to the BAP for this session. |
| `connectorType` | `string` (enum) | — | Connector used for this session: `CCS2`, `Type2`, `CHAdeMO`, `GB_T`. |
| `maxPowerKW` | `number` | — | Peak power observed/allowed for this session (kW). |
| `meteredEnergyKWh` | `number` | — | Total metered energy delivered (kWh). |
| `meteredDurationMinutes` | `number` | — | Total metered duration of the session (minutes). |
| `totalCost` | `PriceSpecification` | — | Total cost of the charging session. |
| `authorizationMode` | `string` (enum) | — | How the session was authorized (e.g., `RFID`, `APP`, `PLUG_AND_CHARGE`). |
| `telemetry` | `array<TelemetryInterval>` | — | Time-series telemetry readings during the session. |
| `trackingUrl` | `string` (uri) | — | URL for real-time session tracking. |

## Linked Data

| Resource | URL |
|----------|-----|
| Canonical IRI | `https://schema.nfh.global/EvChargingSession` |
| JSON Schema (latest) | `https://schema.nfh.global/EvChargingSession/v2.0` |
| context.jsonld (latest) | `https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld` |
| vocab.jsonld (latest) | `https://schema.nfh.global/EvChargingSession/v2.0/vocab.jsonld` |
| Root context.jsonld | `https://schema.nfh.global/context.jsonld` |
| Root vocab.jsonld | `https://schema.nfh.global/vocab.jsonld` |
