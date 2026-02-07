# DEG Contract Examples

Example Beckn Protocol v2 message flows showing the **DEGContract-as-Code** schema in action. Each subdirectory contains a complete transaction lifecycle from discovery through settlement.

## Directory Structure

```
deg_contract/
├── ev_charging/              # Standard EV charging contract
├── p2p-trading-interdiscom/  # Inter-discom P2P energy trade (with cascaded utility init)
└── smart_ev_charging/        # Composite: EV charging + V2G demand flexibility
```

## How DEGContract Maps to Beckn Slots

| Beckn Lifecycle | DEGContract State | Where DEGContract Lives |
|----------------|-------------------|------------------------|
| `on_search` (catalog) | TEMPLATE | `Offer.offerAttributes.degContract` |
| `select` | TEMPLATE → NEGOTIATED | `Order.orderAttributes.degContract` |
| `on_select` (quote) | NEGOTIATED | `Order.orderAttributes.degContract` |
| `init` / `on_init` | COMMITTED | `Order.orderAttributes.degContract` |
| `confirm` / `on_confirm` | ACTIVE | `Order.orderAttributes.degContract` |
| `status` / `on_status` | ACTIVE (with fulfillment data) | `Order.orderAttributes.degContract` |
| `on_status` (final) | SETTLED | `Order.orderAttributes.degContract` (with `revenueModel.flows[].computedAmount`) |

## Key Patterns

### 1. Partially-Filled Templates
In the catalog (`on_discover`), the DEGContract is a **template** with:
- Provider/seller roles **filled** (their inputs pre-populated)
- Consumer/buyer roles **open** (`party: null`, inputs unfilled)

### 2. Progressive Role Filling
As the transaction progresses:
- `select`: Buyer fills negotiation-phase inputs (quantity, preferences)
- `init`: Buyer fills commitment-phase inputs (meter ID, billing, credentials)
- `confirm`: All roles filled, contract becomes ACTIVE

### 3. Revenue Model & Net-Zero Invariant
Every contract includes a `revenueModel` with directed monetary flows:
- At discovery: flows show **formulas** (how amounts are computed)
- At settlement: flows show **computedAmount** (actual INR values)
- The **net-zero invariant** ensures `sum(all flows) == 0`

### 4. Policy References
Contract terms reference Rego policies for complex logic:
```yaml
condition:
  policyRef:
    type: REGO
    package: "deg.contracts.ev_charging"
    entrypoint: "connector_compatible"
```
See `specification/policies/` for the Rego policy files.

## Related Files

- **Schema**: `specification/schema/deg_contract_schema.yaml`
- **Policies**: `specification/policies/*.rego`
- **Arazzo Workflow**: `specification/deg_contract_beckn_flow.arazzo.yaml`
- **Specification**: `docs/implementation-guides/deg_contract/DEG_Contract_Specification.md`
- **Mapping Guide**: `docs/implementation-guides/deg_contract/Mapping_Existing_Schemas.md`
