# EvChargingCommitment v1.0

The driver's charging request and the CPO's answer to it, attached to `Commitment.commitmentAttributes`. The energy needed travels on the core `Commitment.resources[].quantity` (`unitCode: KWH`).

| Property | Written by | From | Required | Description |
|---|---|---|:-:|---|
| `vehicle.maxChargeKW` | driver | select | ✓ | Maximum power the vehicle accepts; bounds `quote.promisedKW` |
| `vehicle.socPercent` | driver | select | — | State of charge; forecast input |
| `reservedStart` | driver | select | RESERVATION only | Reserved start; at least the network's lead time ahead (N3) |
| `quote.promisedKW` | CPO | on_select | ✓ | Contractual reference power for delay and shortfall |
| `quote.estimatedStart.from` / `.to` | CPO | on_select | ✓ | Forecast band for stall assignment; may be refreshed on any on_status |

```json
"commitmentAttributes": {
  "@context": "https://raw.githubusercontent.com/ameetdesh/DEG/refs/heads/main/specification/schema/EvChargingCommitment/v1.0/context.jsonld",
  "@type": "ChargingCommitment",
  "vehicle": {"maxChargeKW": 60, "socPercent": 22},
  "reservedStart": "2026-10-02T18:00:00Z",
  "quote": {"promisedKW": 60, "estimatedStart": {"from": "2026-10-02T18:00:00Z", "to": "2026-10-02T18:10:00Z"}}
}
```

Used by [devkits/ev-charging/uc2-ev-charging](../../../../devkits/ev-charging/uc2-ev-charging/).
