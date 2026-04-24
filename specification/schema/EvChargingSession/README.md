# EvChargingSession

> **Canonical IRI:** [`https://schema.beckn.io/EvChargingSession`](https://schema.beckn.io/EvChargingSession)
> **Tags:** `ev-charging, session, fulfillment, telemetry, billing, reservation, ocpp, energy, beckn`
> **Namespace:** `https://schema.beckn.io/`
> Part of the [DEG Schema](../../README.md)

---

**EV charging session attributes** attached to `Order.fulfillments[].attributes` in a Beckn EV-charging transaction. Captures real-time or completed charging session data — including session status, energy consumed, duration, total cost, telemetry intervals, and tracking links.

## Versions

| Version | attributes.yaml | context.jsonld | vocab.jsonld | README |
|---------|----------------|----------------|--------------|--------|
| **v1.0** | [attributes.yaml](./v1.0/attributes.yaml) | [context.jsonld](./v1.0/context.jsonld) | [vocab.jsonld](./v1.0/vocab.jsonld) | [README](./v1.0/README.md) |
| **v2.0** | [attributes.yaml](./v2.0/attributes.yaml) | [context.jsonld](./v2.0/context.jsonld) | [vocab.jsonld](./v2.0/vocab.jsonld) | [README](./v2.0/README.md) |

## Properties (latest: v2.0)

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `sessionStatus` | `string` (enum) | — | High-level session state: `PENDING`, `ACTIVE`, `STOP`, `COMPLETED`, `INTERRUPTED`. |
| `connectorStatus` | `string` (enum) | — | Charging connector status (OCPP codes): `AVAILABLE`, `PREPARING`, `UNAVAILABLE`. |
| `buyerFinderFee` | `object` | — | Commission payable by provider to the BAP for this session. |
| `connectorType` | `string` (enum) | — | Connector used for this session. Full list: see [ConnectorType](../ConnectorType/README.md). |
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
| Canonical IRI | `https://schema.beckn.io/EvChargingSession` |
| JSON Schema (latest) | `https://schema.beckn.io/EvChargingSession/v2.0` |
| context.jsonld (latest) | `https://schema.beckn.io/EvChargingSession/v2.0/context.jsonld` |
| vocab.jsonld (latest) | `https://schema.beckn.io/EvChargingSession/v2.0/vocab.jsonld` |
| Root context.jsonld | `https://schema.beckn.io/context.jsonld` |
| Root vocab.jsonld | `https://schema.beckn.io/vocab.jsonld` |
