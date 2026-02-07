# DEG Contract Examples

Example Beckn Protocol v2 message flows showing the **DEGContract-as-Code** schema in action. Each subdirectory contains a complete transaction lifecycle from discovery through settlement.

## Directory Structure

```
deg_contract/
├── ev_charging/              # Standard EV charging contract (9 files)
├── p2p-trading-interdiscom/  # Inter-discom P2P energy trade with cascaded utility init (11 files)
└── smart_ev_charging/        # Composite: EV charging + V2G demand flexibility (10 files)
```

## Pure Beckn Slot Mapping

DEGContract is the **primary `@type`** in `offerAttributes` and `orderAttributes`. Domain-specific data lives in dedicated Beckn attribute slots using first-principles schemas.

| Beckn Slot | `@type` | Purpose | First Appears |
|------------|---------|---------|--------------|
| `itemAttributes` | **EnergyResource** | Physical resource: charger, solar plant, battery | `on_discover` |
| `offerAttributes` | **DEGContract** (TEMPLATE) | Contract template with open role slots | `on_discover` |
| `providerAttributes` | **EnergyProvider** | Provider identity, registration, grid account | `on_discover` |
| `buyerAttributes` | **EnergyBuyer** | Buyer vehicle info or grid account | `select` |
| `orderAttributes` | **DEGContract** (NEGOTIATED→SETTLED) | Contract through full lifecycle | `select` onwards |
| `deliveryAttributes` | **EnergyDelivery** | Runtime telemetry, session state, V2G events | `on_confirm` |
| `paymentAttributes` | **PaymentSettlement** | Settlement accounts & reconciliation | `init` |

### Schema Design Principles

- **One unified `EnergyResource`** with `resourceType` enum (EV_CHARGER, GENERATION_PLANT, BATTERY_STORAGE, GRID_CONNECTION) — not separate schemas per domain
- **One unified `EnergyDelivery`** with sparse sub-objects (`v2g`, `grid`, `vehicle`, `meterReadings`) — consumers check `deliveryMode` to know which are present
- **DEGContract absorbs commercial terms** — tariffModel, idleFeePolicy, pricingModel etc. are expressed in `terms[]` and `revenueModel.flows[]`, not in wrapper schemas
- **Buyer billing stays in `beckn:Buyer`** — EnergyBuyer only adds domain-specific info (vehicle, grid account)

## How DEGContract Maps to Beckn Lifecycle

| Beckn Action | DEGContract State | What Changes |
|-------------|-------------------|-------------|
| `on_discover` (catalog) | **TEMPLATE** | Provider roles filled, buyer roles open (`party: null`) |
| `select` | TEMPLATE → **NEGOTIATED** | Buyer fills quantity, preferences |
| `on_select` (quote) | **NEGOTIATED** | BPP returns computed pricing |
| `init` / `on_init` | **COMMITTED** | Buyer fills meter ID, billing, credentials |
| `confirm` / `on_confirm` | **ACTIVE** | All roles filled, `deliveryAttributes` appears (PENDING) |
| `on_status` | **ACTIVE** | `deliveryAttributes` updated with telemetry |
| `on_update` | **ACTIVE** | V2G events, demand flex triggers |
| `on_status` (final) / `on_update` (complete) | **SETTLED** | `computedAmount` in all revenue flows, net-zero verified |

## Key Patterns

### 1. Progressive Role Filling
In the catalog (`on_discover`), the DEGContract is a **template** with:
- Provider/seller roles **filled** (their inputs pre-populated)
- Consumer/buyer roles **open** (`party: null`, inputs unfilled)

As the transaction progresses, the buyer progressively fills their role inputs.

### 2. Revenue Model & Net-Zero Invariant
Every contract includes a `revenueModel` with directed monetary flows:
- At discovery: flows show **formulas** (how amounts are computed)
- At settlement: flows show **computedAmount** (actual INR values)
- **Conservation law**: for every party, `sum(inflows) - sum(outflows)` across ALL parties = 0

### 3. Policy References (Contract-as-Code)
Contract terms reference OPA/Rego policies for complex logic:
```json
{
  "condition": {
    "policyRef": {
      "type": "REGO",
      "package": "deg.contracts.ev_charging",
      "entrypoint": "connector_compatible"
    }
  }
}
```
See `specification/policies/` for the Rego policy files.

### 4. Composite Contracts
Smart EV charging uses `contractType: "COMPOSITE"` with `composedOf: ["EV_CHARGING", "DEMAND_FLEXIBILITY"]` — combining EV charging and V2G grid services in one contract.

## Use Cases

### EV Charging (`ev_charging/`, 9 files)
- **Roles**: `cpo` (CPO) + `ev_driver` (CONSUMER)
- **Revenue**: charging_payment + platform_fee + GST + idle_fee - refund_overcharge
- **Resource**: EV_CHARGER, CCS2 DC fast charger at ChargeZone Bangalore

### P2P Inter-Discom Trading (`p2p-trading-interdiscom/`, 11 files)
- **Roles**: `seller` (PRODUCER) + `buyer` (CONSUMER) + `source_utility` (DISCOM) + `destination_utility` (DISCOM)
- **Revenue**: energy_payment + wheeling_charge(×2) + platform_fee(×2) + deviation_penalty
- **Resource**: GENERATION_PLANT, 10 kW rooftop solar in Delhi
- **Special**: Cascaded init (P2P BPP acts as BAP to utility BPP for wheeling approval)

### Smart EV Charging + V2G (`smart_ev_charging/`, 10 files)
- **Roles**: `ev_owner` (PROSUMER) + `cpo_aggregator` (AGGREGATOR) + `grid_operator` (GRID_OPERATOR)
- **Revenue**: charging_payment - v2g_earnings + grid_v2g_payment + platform_fee
- **Resource**: EV_CHARGER with V2G capability, Tata EZ Charge Hub Mumbai
- **Special**: V2G dispatch on grid frequency < 49.5 Hz, Rego policy evaluation inline

## Related Files

- **Schema**: `specification/schema/deg_contract_schema.yaml`
- **Policies**: `specification/policies/*.rego`
- **Arazzo Workflow**: `specification/deg_contract_beckn_flow.arazzo.yaml`
- **Specification**: `docs/implementation-guides/deg_contract/DEG_Contract_Specification.md`
- **Mapping Guide**: `docs/implementation-guides/deg_contract/Mapping_Existing_Schemas.md`
