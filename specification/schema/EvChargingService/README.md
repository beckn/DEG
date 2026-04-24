# EvChargingService

> **Canonical IRI:** [`https://schema.beckn.io/EvChargingService`](https://schema.beckn.io/EvChargingService)
> **Tags:** `ev-charging, item, connector, station, ocpp, ocpi, power, reservation, energy, beckn`
> **Namespace:** `https://schema.beckn.io/`
> Part of the [DEG Schema](../../README.md)

---

**EV charging service attributes** attached to `Item.attributes` in a Beckn EV-charging catalog. Captures technical and contextual details of a charging connector or station — including connector type, power capacity, socket count, reservation capability, and amenities.

## Versions

| Version | attributes.yaml | context.jsonld | vocab.jsonld | README |
|---------|----------------|----------------|--------------|--------|
| **v1.0** | [attributes.yaml](./v1.0/attributes.yaml) | [context.jsonld](./v1.0/context.jsonld) | [vocab.jsonld](./v1.0/vocab.jsonld) | [README](./v1.0/README.md) |
| **v2.0** | [attributes.yaml](./v2.0/attributes.yaml) | [context.jsonld](./v2.0/context.jsonld) | [vocab.jsonld](./v2.0/vocab.jsonld) | [README](./v2.0/README.md) |

## Properties (latest: v2.0)

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `evseId` | `string` | — | EVSE identifier (e.g., OCPI/Hubject style). |
| `qrIdentifier` | `string` | — | Short URL or token encoded in the physical QR code affixed to the connector, for BAP-side QR-scan discovery. |
| `connectorType` | `string` (enum) | ✓ | Physical connector type. Full list: see [ConnectorType](../ConnectorType/README.md). |
| `maxPowerKW` | `number` | ✓ | Maximum output power of the connector (kW). |
| `minPowerKW` | `number` | — | Minimum controllable power if throttling is supported (kW). |
| `reservationSupported` | `boolean` | — | Whether advance reservations are supported. |
| `chargingStation` | `object` | — | Charging station information including station ID and location. |
| `socketCount` | `integer` | — | Number of sockets at this EVSE. |
| `amenities` | `array<string>` | — | Available amenities at or near the charging location. |
| `roamingNetworks` | `array<string>` | — | Interoperability/roaming networks this EVSE participates in. |
| `ocppVersion` | `string` | — | OCPP protocol version supported. |
| `powerType` | `string` (enum) | — | AC or DC power type. |
| `vehicleType` | `string` or `array<string>` (enum) | — | Vehicle type(s) that can use this charging service: `2-WHEELER`, `3-WHEELER`, `4-WHEELER`. |

## Linked Data

| Resource | URL |
|----------|-----|
| Canonical IRI | `https://schema.beckn.io/EvChargingService` |
| JSON Schema (latest) | `https://schema.beckn.io/EvChargingService/v2.0` |
| context.jsonld (latest) | `https://schema.beckn.io/EvChargingService/v2.0/context.jsonld` |
| vocab.jsonld (latest) | `https://schema.beckn.io/EvChargingService/v2.0/vocab.jsonld` |
| Root context.jsonld | `https://schema.beckn.io/context.jsonld` |
| Root vocab.jsonld | `https://schema.beckn.io/vocab.jsonld` |
