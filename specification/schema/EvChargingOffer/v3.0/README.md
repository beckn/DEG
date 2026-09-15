# EvChargingOffer v3.0

Settlement-first EV charging offer, attached to `Offer.offerAttributes`. An offer publishes:

- a contract **mode** (`WALK_IN` or `RESERVATION`);
- the complete **terms** the contract policy settles against;
- the **DEGContract template** (roles `cpo` / `driver`, policy reference), copied to `Contract.contractAttributes` at select.

The policy holds the formulas and every number is in `terms`, so CPOs compete on terms while the network standardises the rules. v3.0 is a clean break from v2.0 (`tariffModel`, `idleFeePolicy`, `buyerFinderFee`), which remains valid.

| Property | Type | Required | Description |
|---|---|:-:|---|
| `mode` | `WALK_IN` \| `RESERVATION` | ✓ | Contract mode |
| `terms.currency` | ISO 4217 | ✓ | Currency of every amount (tax-exclusive) |
| `terms.energyPerKWh` | number | ✓ | Energy tariff |
| `terms.occupancyPerMin` | number | ✓ | Stall rent per driver-responsible minute |
| `terms.idlePerMin` | number | ✓ | Idle fee per minute beyond `graceMin` |
| `terms.graceMin` | integer | ✓ | Arrival, unplugging and CPO-readiness slack |
| `terms.maxDemotions` | integer | ✓ | Missed assignments tolerated before `NO_SHOW` |
| `terms.gridDelayCreditPerMin` | number | ✓ | Credit per minute added by grid limits |
| `terms.reservation.fee` | number | RESERVATION | Reservation premium |
| `terms.reservation.cancelBeforeMin` | integer | RESERVATION | Free cancellation window before `reservedStart` |
| `terms.reservation.cpoDelayCreditPerMin` | number | RESERVATION | Credit per minute of CPO-caused delay |
| `terms.reservation.liabilityCap` | number | RESERVATION | Cap on the CPO delay credit |
| `contractAttributes` | DEGContract | ✓ | Contract template |

`mode` and the presence of `terms.reservation` must agree (network policy N2).

```json
"offerAttributes": {
  "@context": "https://raw.githubusercontent.com/ameetdesh/DEG/refs/heads/main/specification/schema/EvChargingOffer/v3.0/context.jsonld",
  "@type": "ChargingOffer",
  "mode": "RESERVATION",
  "terms": {
    "currency": "INR", "energyPerKWh": 18, "occupancyPerMin": 2, "idlePerMin": 10, "graceMin": 5, "maxDemotions": 2, "gridDelayCreditPerMin": 1,
    "reservation": {"fee": 100, "cancelBeforeMin": 60, "cpoDelayCreditPerMin": 5, "liabilityCap": 500}
  },
  "contractAttributes": {
    "@context": "https://schema.nfh.global/DEGContract/v2.0/context.jsonld", "@type": "DEGContract",
    "roles": [{"role": "cpo", "participantId": "bpp.example.com"}, {"role": "driver", "participantId": null}],
    "policy": {"url": "https://raw.githubusercontent.com/ameetdesh/DEG/refs/heads/main/specification/policies/ev-charging-contractpolicy.rego", "queryPath": "data.deg.contracts.ev_charging"}
  }
}
```

Used by [devkits/ev-charging/uc2-ev-charging](../../../../devkits/ev-charging/uc2-ev-charging/).
