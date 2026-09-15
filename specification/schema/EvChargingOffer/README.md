# EvChargingOffer

> **Canonical IRI:** [`https://schema.nfh.global/EvChargingOffer`](https://schema.nfh.global/EvChargingOffer)
> **Tags:** `ev-charging, offer, tariff, pricing, idle-fee, energy, beckn`
> **Namespace:** `https://schema.nfh.global/`
> Part of the [DEG Schema](../../README.md)

---

**EV charging offer attributes** attached to `Offer.attributes` in a Beckn EV-charging catalog. Captures tariff details beyond core price fields — including per-kWh or time-based pricing models, idle fee policies, and accepted payment methods.

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
| `tariffModel` | `string` (enum) | — | Tariff model classification: `PER_KWH`, `PER_MINUTE`, `SUBSCRIPTION`, `TIME_OF_DAY`. |
| `idleFeePolicy` | `PriceSpecification` | — | Idle fee policy — charge applied after session ends but vehicle remains plugged in. |
| `buyerFinderFee` | `object` | — | Commission payable by the provider to the BAP for this offer. |
| `eligibleQuantity` | `Quantity` | — | Energy quantity limits (min/max kWh) applicable to this offer. |
| `acceptedPaymentMethods` | `array<string>` | — | List of accepted payment method codes (e.g., `UPI`, `CARD`). |

## Linked Data

| Resource | URL |
|----------|-----|
| Canonical IRI | `https://schema.nfh.global/EvChargingOffer` |
| JSON Schema (latest) | `https://schema.nfh.global/EvChargingOffer/v2.0` |
| context.jsonld (latest) | `https://schema.nfh.global/EvChargingOffer/v2.0/context.jsonld` |
| vocab.jsonld (latest) | `https://schema.nfh.global/EvChargingOffer/v2.0/vocab.jsonld` |
| Root context.jsonld | `https://schema.nfh.global/context.jsonld` |
| Root vocab.jsonld | `https://schema.nfh.global/vocab.jsonld` |
