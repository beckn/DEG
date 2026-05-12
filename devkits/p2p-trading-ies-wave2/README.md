# P2P Trading (Wave 2) Devkit

Beckn Protocol v2.0 LTS devkit for **inter-discom Peer-to-Peer energy trading**. Two prosumers on different discoms trade energy directly, with each discom represented in the protocol by a regulated Ledger Provider (`buyerDiscom`, `sellerDiscom`). The contract names four roles and an OPA/rego policy computes net `revenueFlows`. Wave 2 supersedes [`p2p-trading-ies-wave1`](../p2p-trading-ies-wave1/) — same scenario, but built on `core-v2.0.0-lts`, the latest onix-adapter, and the `contractAttributes` framework already used by [`demand-flex`](../demand-flex/).

For the shared stack topology, prerequisites, Quick Start, transaction flow, hosting, ngrok notes, and cleanup, see [../README.md](../README.md).

## Scenario

A rooftop solar prosumer on **TPDDL** (the seller, BPP-side) lists a 1-hour delivery slot of 30 kWh at 12 INR/kWh. A prosumer on **BRPL** (the buyer, BAP-side) discovers the offer, selects 20 kWh, optionally pre-checks discom-ledger headroom on both sides, confirms, and after physical delivery the Seller TP publishes settled qty. The linked rego computes revenueFlows summing to zero across buyer / seller / buyerDiscom / sellerDiscom — wheeling charges and penalty charges are zero placeholders today, but the structure is wired so a future tariff/penalty rule can be plugged in without re-shaping the payload or callers.

## Use Cases

| Use Case | BPP (Seller TP) | BAP (Buyer TP) | Description |
|----------|-----------------|----------------|-------------|
| [uc1](./uc1/) | Prosumer on TPDDL | Prosumer on BRPL | Publish offer → discover → select → optional discom-limit check → confirm → settle |

## Roles

The contract names four conceptual actors. Only buyer and seller speak Beckn directly in the minimal flow; buyerDiscom and sellerDiscom are present in `contractAttributes.roles` so the rego can compute net revenueFlows that include wheeling charges. The optional Phase 2 step demonstrates the discom-ledger limit check.

| Role | participantId | Acts as |
|------|---------------|---------|
| `buyer` | `example.bap.com` | Buyer prosumer's TP (BAP) |
| `seller` | `example.bpp.com` | Seller prosumer's TP (BPP) |
| `buyerDiscom` | `buyer-discom-ledger` | Regulated Ledger Provider for buyer's discom |
| `sellerDiscom` | `seller-discom-ledger` | Regulated Ledger Provider for seller's discom |

## Key Schemas

| Schema | Slot | Description |
|--------|------|-------------|
| [P2PTrade](../../specification/schema/P2PTrade/v2.0/) | `message.contract` `@type` | Current P2P trading contract type (subclass of `EnergyContract`) |
| [EnergyResource](../../specification/schema/EnergyResource/v2.0/) | `resourceAttributes` | Source type (SOLAR/BATTERY/…) and meterId |
| [EnergyTradeOffer](../../specification/schema/EnergyTradeOffer/v2.0/) | `offerAttributes` | Pricing model, validity / delivery window |
| [EnergyTradeDelivery](../../specification/schema/EnergyTradeDelivery/v2.0/) | `performance.performanceAttributes` | Delivery status, meter readings, settled qty |
| [DEGContract](../../specification/schema/DEGContract/v2.0/) | `contractAttributes` | Roles, policy reference, computed revenueFlows |
| [DiscomLedgerProvider](../../specification/schema/DiscomLedgerProvider/v1.0/) | `participants[role=buyerDiscom\|sellerDiscom].participantAttributes` | Discom ledger TSP identity — `utilityId` + `ledgerUri` so the `degledgerrecorder` plugin can pick the right ledger URL per discom from the payload |

## Postman

`uc1/postman/p2p-trading-ies-wave2-uc1.{BAP,BPP}-DEG.postman_collection.json`. Collections are regenerated with `python3 scripts/generate_postman_collection.py --role BAP|BPP`.

## Policy Enforcement

Two layers, both via the `opapolicychecker` plugin:

- **Network policy** — declared in [`config/opa-network-policies.yaml`](./config/opa-network-policies.yaml) and loaded from [`policies/p2p-trading-ies-wave2_network.rego`](./policies/p2p-trading-ies-wave2_network.rego) (mirrors [`specification/policies/p2p-trading-ies-wave2_network.rego`](../../specification/policies/p2p-trading-ies-wave2_network.rego)). Both BAP and BPP use a single `default:` entry — every message evaluates against the same rules regardless of `context.networkId`. Add per-networkId entries as the network matures.
- **Contract policy** — every payload's `contractAttributes.policy.url` points to [`specification/policies/p2p_trading_ies_wave2_revenue.rego`](../../specification/policies/p2p_trading_ies_wave2_revenue.rego). The rego computes a four-role `revenueFlows` array from the seller's `inputs.offers[0].pricePerKwh` and the settled quantity. The on-status payload carries the result at `message.contract.consideration[0].considerationAttributes` (RevenueFlow JSON-LD, Beckn-native). Wheeling and penalty charges are `0` placeholders in the rego today — flip them to real expressions when the tariff/penalty rules land; no payload changes needed. (The legacy BPP-side `revenueflows` middleware that auto-injected into `contractAttributes` is currently disabled — see `config/local-p2p-trading-bpp.yaml` — until it can target the consideration block.)

Signature/registry lookups currently target `nfh.global/testnet-deg` via the `allowedNetworkIDs` key on the `dediregistry` plugin. Subscriber IDs are placeholders (`bap.example.com` / `bpp.example.com`) with signing keys borrowed from the p2p-trading devkit, so arazzo flows will NACK on lookup until real subscribers are registered on testnet-deg.

## Ledger recording

On `on_confirm` both platforms write a trade record to their own discom's ledger TSP via the [`degledgerrecorder`](../../plugins/degledgerrecorder/) plugin:
- BAP-Receiver runs the plugin with `role: BUYER` and reads `participants[role=buyerDiscom].participantAttributes.ledgerUri` from the payload.
- BPP-Caller runs the plugin with `role: SELLER` and reads `participants[role=sellerDiscom].participantAttributes.ledgerUri` from the payload.

Both URIs are wired in the example payloads to the IES ledger service (`https://ies-p2p-energy-ledger.beckn.io`); two discoms MAY share a TSP — each platform still writes only to its own side.

Mode flags in the [BAP](./config/local-p2p-trading-bap.yaml) and [BPP](./config/local-p2p-trading-bpp.yaml) configs: `payloadShape: wave2`, `ledgerUriSource: payload`, `ledgerApi: legacy_ledger`. Flip `ledgerApi` to `beckn` once the ledger TSP is upgraded to accept beckn `on_confirm`.

## Related

- [Inter Energy Retailer P2P Trading Implementation Guide](../../docs/implementation-guides/v2/P2P_Trading/Inter_energy_retailer_P2P_trading.md) — Sequence diagram, ledger data structures, reconciliation logic
- [P2PTrade Schema](../../specification/schema/P2PTrade/v2.0/) — Contract type
- [EnergyTrade Schema (deprecated)](../../specification/schema/EnergyTrade/v2.0/) — Predecessor; kept for backward compatibility
- [Demand Flex Devkit](../demand-flex/) — Sister devkit on the same v2 LTS / OPA / contractAttributes shape
- [P2P Trading (Wave 1) Devkit](../p2p-trading-ies-wave1/) — Predecessor on `core-2.0.0-rc-eos-release` with the older `beckn:Order` / `EnergyTrade v0.3` shape
