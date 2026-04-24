# Demand Flex Devkit

Beckn Protocol v2.0 devkit for **behavioral demand response**. A utility publishes flexibility needs (peak demand reduction), and aggregators discover, commit to, and deliver demand flexibility — with settlement based on measured performance.

For the shared stack topology, prerequisites, Quick Start, transaction flow, hosting, ngrok notes, and cleanup, see [../README.md](../README.md).

## Scenario

**TPDDL** (Tata Power Delhi Distribution, the utility) publishes a 500 kW curtailment need during a peak event window. **GreenFlex Aggregator** discovers the opportunity, enrolls participating meters, and commits to providing 150 kW of demand reduction. After the event, TPDDL publishes baselines, measured actuals, and computes settlement (e.g., 150 kWh x 3.5 INR/kWh = 525 INR).

## Use Cases

| Use Case | BPP (Provider) | BAP (Consumer) | Description |
|----------|---------------|----------------|-------------|
| [uc1-demand-flex](./uc1-demand-flex/) | TPDDL (utility) | GreenFlex (aggregator) | Publish flex need → discover → commit → deliver → settle |

## Key Schemas

| Schema | Slot | Description |
|--------|------|-------------|
| [DemandFlexNeed](../../specification/schema/DemandFlexNeed/v2.0/) | `resourceAttributes` | Direction (REDUCE/INCREASE), event window, capacity type, location |
| [DemandFlexBuyOffer](../../specification/schema/DemandFlexBuyOffer/v2.0/) | `offerAttributes` | Incentive per kWh, baseline methodology, penalty rate |
| [DEGContract](../../specification/schema/DEGContract/v2.0/) | `contractAttributes` | Roles (buyer/seller), policy reference, revenue flows |
| [DemandFlexPerformance](../../specification/schema/DemandFlexPerformance/v2.0/) | `performanceAttributes` | M&V baselines and actuals per meter |

## Postman

`uc1-demand-flex/postman/demand-flex-uc1-demand-flex.{BAP,BPP}-DEG.postman_collection.json`. Collections are regenerated with `python3 scripts/generate_postman_collection.py --role BAP|BPP`.

## Policy Enforcement

Uses OPA (Open Policy Agent) via the `opapolicychecker` plugin. Policies are declared in [`config/opa-network-policies.yaml`](./config/opa-network-policies.yaml) and loaded from [`policies/demand_flex_network.rego`](./policies/demand_flex_network.rego) (a no-op placeholder that mirrors [`specification/policies/demand_flex_network.rego`](../../specification/policies/demand_flex_network.rego)). Both BAP and BPP use a single `default:` entry — every message evaluates against the same rules regardless of `context.networkId`. Add per-networkId entries to `opa-network-policies.yaml` as the demand-flex network matures.

Signature/registry lookups currently target `nfh.global/testnet-deg` via the `allowedNetworkIDs` key on the `dediregistry` plugin. Subscriber IDs are placeholders (`bap.example.com` / `bpp.example.com`) with signing keys borrowed from the p2p-trading devkit, so arazzo flows will NACK on lookup until real subscribers are registered on testnet-deg.

## Related

- [DemandFlexNeed Schema](../../specification/schema/DemandFlexNeed/v2.0/) — Flex resource attributes
- [DemandFlexBuyOffer Schema](../../specification/schema/DemandFlexBuyOffer/v2.0/) — Incentive and policy terms
- [Demand Flexibility Implementation Guide](../../docs/implementation-guides/v2/Demand_Flexibility/Demand_Flexibility.md) — Detailed protocol flows and schema mappings
- [Data Exchange Devkit](../data-exchange/) — Companion devkit for energy data delivery
