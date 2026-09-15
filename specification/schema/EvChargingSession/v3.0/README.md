# EvChargingSession v3.0

An EV charging session recorded as a **transition log**, attached to `Performance.performanceAttributes`. This is the ledger the contract policy settles from.

Each row holds its state from `at` until the next row's `at`, so time is conserved and intervals are contiguous by construction. The state name carries attribution (`LIMITED_BY_CPO`, `LIMITED_BY_GRID`), and the stall is named on the `ASSIGNED` row. v3.0 is a clean break from v2.0 (`sessionStatus`, `chargingTelemetry`), which remains valid.

| Row field | Required | Description |
|---|:-:|---|
| `at` | ✓ | Moment the session entered the state (UTC) |
| `state` | ✓ | One of the ten states below |
| `stallId` | on `ASSIGNED` only | EVSE assigned to the driver |
| `kWh` | on energy states only | Metered register delta over the row |
| `eventId` | on `LIMITED_BY_GRID` only | Grid event behind the limit |

| State | Meaning |
|---|---|
| `QUEUED` | In the virtual queue, no stall |
| `ASSIGNED` | Stall held for the driver; arrival grace running |
| `CHARGING` | On stall; pace set by the vehicle (including pauses) |
| `LIMITED_BY_CPO` | On stall; power limited by the CPO (derate, fault, site load) |
| `LIMITED_BY_GRID` | On stall; power limited by a grid event |
| `IDLE` | Charging finished; vehicle still on the stall |
| `DEPARTED` · `CANCELLED` · `NO_SHOW` · `FAILED_BY_CPO` | Terminal |

Legal transitions and conditional fields are enforced by [ev-charging-networkpolicy.rego](../../../policies/ev-charging-networkpolicy.rego) (N5–N7). The state diagram is in [uc2 DESIGN.md §5](../../../../devkits/ev-charging/uc2-ev-charging/DESIGN.md#5-session-state-machine).

```json
"performanceAttributes": {
  "@context": "https://raw.githubusercontent.com/ameetdesh/DEG/refs/heads/main/specification/schema/EvChargingSession/v3.0/context.jsonld",
  "@type": "ChargingSession",
  "ledger": [
    {"at": "2026-10-02T12:05:00Z", "state": "QUEUED"},
    {"at": "2026-10-02T18:12:00Z", "state": "ASSIGNED", "stallId": "IN*ECO*E01BTM*A1"},
    {"at": "2026-10-02T18:15:00Z", "state": "CHARGING", "kWh": 10.0},
    {"at": "2026-10-02T18:55:00Z", "state": "IDLE"},
    {"at": "2026-10-02T19:04:00Z", "state": "DEPARTED"}
  ]
}
```
