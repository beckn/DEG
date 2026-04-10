# Demand Flex Devkit

## Goal

This devkit enables developers to prototype and test **behavioral demand response** (demand-flex) workflows on the Beckn protocol. A utility publishes flex needs on the network, and consumers or aggregators discover, select, and commit to providing demand flexibility during peak events.

The devkit includes:
- Pre-configured Beckn ONIX adapters (BAP + BPP) with OPA policy checking
- Sandbox applications for simulating consumer and utility endpoints
- Postman collections covering the full contract lifecycle
- Schema-validated example payloads for every API action

## Architecture

```
┌─────────────┐         ┌──────────┐         ┌─────────────┐
│  Sandbox BAP │◄───────►│ ONIX BAP │◄───────►│  ONIX BPP   │◄───────►│ Sandbox BPP │
│  (Consumer)  │  :3001  │  :8081   │         │   :8082     │  :3002  │  (Utility)  │
└─────────────┘         └──────────┘         └─────────────┘         └─────────────┘
                              │                     │
                              └────── Redis ────────┘
                                     :6379
```

**Message flow:**
1. Utility (BPP) publishes flex catalog via `catalog_publish`
2. Consumer (BAP) discovers and selects offers via `select`
3. Consumer provides identity at `init`, confirms at `confirm`
4. Consumer updates participating meters via `update`
5. Utility sends baselines and actuals via `on_status`

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Git](https://git-scm.com/)
- [Postman](https://www.postman.com/downloads/) (for testing API flows)

## Setup

```bash
# Clone the repo
git clone https://github.com/beckn/DEG.git
cd DEG
git checkout p2p-trading-becknv2

# Navigate to devkit
cd testnet/demand-flex-devkit
```

### Upstream Projects

| Component | Repository | Image |
|:----------|:-----------|:------|
| ONIX Adapter | [beckn/beckn-onix](https://github.com/beckn/beckn-onix) | `fidedocker/onix-adapter:1.5.0` |
| Sandbox | [beckn/beckn-sandbox](https://github.com/beckn/beckn-sandbox) | `fidedocker/sandbox-2.0:latest` |

## Running the Test Network

### 1. Start services

```bash
cd install
docker compose -f docker-compose-demand-flex.yml up -d
```

Verify all containers are running:
```bash
docker compose -f docker-compose-demand-flex.yml ps
```

**Sandbox BPP and `on_*` callbacks:** `sandbox-bpp` merges static JSON from [`sandbox/webhook/jsons/`](sandbox/webhook/jsons/) (mounted at `/app/dist/webhook/jsons` in the container). For domain `beckn.one:deg:demand-flex` it expects files such as `response/on_select.json`, `response/on_update.json`, etc. Those files must include a **`message`** body; otherwise the sandbox forwards **context-only** payloads to `onix-bpp` and you get **400** / `property "message" is missing` from schema validation. The checked-in templates are copied from [`examples/demand-flex/v2/`](../../examples/demand-flex/v2/) with BAP/BPP IDs aligned to this devkit. If bind-mounting fails on Windows (path contains `:`), keep the repo on the WSL filesystem.

### 2. Import Postman collections

Import the following collections into Postman from `postman/`:
- `demand-flex.BAP-DEG.postman_collection.json` (consumer/aggregator flows)
- `demand-flex.BPP-DEG.postman_collection.json` (utility flows)

### 3. Test the flow

Execute requests in this order:

| Step | Collection | Folder | Description |
|:-----|:-----------|:-------|:------------|
| 1 | BPP | publish | Utility publishes flex catalog |
| 2 | BAP | select | Consumer selects a flex offer |
| 3 | BAP | init | Consumer provides identity and taker details |
| 4 | BAP | confirm | Consumer confirms the contract |
| 5 | BAP | update | Consumer sends participating meters |
| 6 | BPP | on_status | Utility sends baselines (pre-event) |
| 7 | BPP | on_status | Utility sends actuals + settlement (post-event) |

### 4. Cleanup

```bash
docker compose -f docker-compose-demand-flex.yml down -v
```

## Configuration

### Environment Variables

| Variable Name | Value | Notes |
|:-------------|:------|:------|
| `domain` | `beckn.one:deg:demand-flex:2.0.0` | |
| `version` | `2.0.0` | Beckn protocol version |
| `bap_id` | `demand-flex-sandbox1.com` | Consumer/aggregator BAP |
| `bpp_id` | `demand-flex-sandbox2.com` | Utility BPP |
| `bap_uri` | `http://onix-bap:8081/bap/receiver` | BAP callback URL |
| `bpp_uri` | `http://onix-bpp:8082/bpp/receiver` | BPP request URL |

**BPP caller (`/bpp/caller/publish`, `on_select`, …):** Put **`subscriber_id`** (snake_case) in `context`, with the **same value as `bppId`** for BPP-originated traffic. For **`on_*`** callbacks to the BAP, [`local-demand-flex-routing-BPP-Caller.yaml`](config/local-demand-flex-routing-BPP-Caller.yaml) sets **`target.url`** under **`targetType: bap`** to `http://onix-bap:8081/bap/receiver` because the sandbox often emits **`bapUri`** (camelCase) only, while the router looks for **`bap_uri`** or a fallback.

**BAP caller (`select`, `init`, …):** Put **`subscriber_id`** (snake_case) in `context`, same value as **`bapId`** (`p2p-trading-sandbox1.com` in this devkit). ONIX does not use **`subscriberId`** (camelCase) for this. The **`bapTxnCaller`** handler in [`local-demand-flex-bap.yaml`](config/local-demand-flex-bap.yaml) also sets **`subscriberId`** in YAML as a default for signing. Routing: [`local-demand-flex-routing-BAP-Caller.yaml`](config/local-demand-flex-routing-BAP-Caller.yaml) **`target.url`** fallback under **`targetType: bpp`** when **`bppUri`** is omitted.

### Config Files

| File | Purpose |
|:-----|:--------|
| [`config/local-demand-flex-bap.yaml`](config/local-demand-flex-bap.yaml) | BAP adapter: registry, keys, schema validation, policy, routing |
| [`config/local-demand-flex-bpp.yaml`](config/local-demand-flex-bpp.yaml) | BPP adapter: same structure, BPP keys and routing |
| [`config/local-demand-flex-routing-*.yaml`](config/) | Routing tables for BAP/BPP receiver and caller modules |

### Policy Enforcement

`fidedocker/onix-adapter-deg` ships the **`policyenforcer`** step (same pattern as the P2P inter-discom devkit), not `checkPolicy` / `opapolicychecker`. Configure it under `plugins.steps` and list `policyenforcer` in the handler `steps` order:

```yaml
        steps:
          - id: policyenforcer
            config:
              policyUrls: "https://raw.githubusercontent.com/beckn/DEG/refs/heads/p2p-trading-becknv2/specification/policies/demand_flex_network.rego"
      steps:
        - validateSign
        - addRoute
        - validateSchema
        - policyenforcer
```

The bundled Rego is a **noop** (no violations). Point `policyUrls` at stricter rules as the network matures.

The `policyenforcer` plugin loads Rego from `policyUrls` and evaluates **`data.deg.policy.violations`** (same as P2P inter-discom). Network rules must live under `package deg.policy` with a `violations` rule set.

**Revenue flows:** The BPP caller config used to enable a `revenueflows` middleware; **`fidedocker/onix-adapter-deg:p2p-multiarch-v6` does not ship that plugin**, so it is commented out in [`local-demand-flex-bpp.yaml`](config/local-demand-flex-bpp.yaml). Re-enable it only with an adapter image that includes `revenueflows`.

### Signing Keys

This devkit reuses the Ed25519 signing keys from the p2p-trading devkit. For production, generate fresh keys:

```bash
# Using Go (from beckn-signing-kit)
go run ./cmd/keygen
```

## Schemas

Domain schemas are hosted on the `p2p-trading-becknv2` branch:

| Schema | Slot | Description |
|:-------|:-----|:------------|
| [DemandFlexNeed](../../specification/schema/DemandFlexNeed/v2.0/) | `resourceAttributes` | Direction, event window, capacity type, location |
| [DemandFlexBuyOffer](../../specification/schema/DemandFlexBuyOffer/v2.0/) | `offerAttributes` | Incentive, penalties, premiums, taker, policy ref |
| [DEGContract](../../specification/schema/DEGContract/v2.0/) | `contractAttributes` | Contract type identifier |
| [DemandFlexPerformance](../../specification/schema/DemandFlexPerformance/v2.0/) | `performanceAttributes` | M&V baselines and actuals per meter |

## Regenerating Postman Collections

```bash
# From repo root
python3 scripts/generate_postman_collection.py \
  --devkit demand-flex --role BAP \
  --output-dir testnet/demand-flex-devkit/postman \
  --name "demand-flex.BAP-DEG" \
  --validate

python3 scripts/generate_postman_collection.py \
  --devkit demand-flex --role BPP \
  --output-dir testnet/demand-flex-devkit/postman \
  --name "demand-flex.BPP-DEG" \
  --validate
```

## Validating Examples

```bash
# From repo root
python3 scripts/validate_schema.py examples/demand-flex/v2/*.json
```

## Troubleshooting

| Issue | Solution |
|:------|:---------|
| Adapter fails to start | Check Redis is healthy: `docker logs redis` |
| Schema validation errors | Ensure schemas are pushed to `p2p-trading-becknv2` branch |
| Policy check fails | Verify the rego URL is accessible: `curl -sI <url>` |
| Port conflicts | Stop other devkits first, or modify port mappings in docker-compose |

## Implementation Guide

See the full [Demand Flexibility Implementation Guide](../../docs/implementation-guides/v2/Demand_Flexibility/Demand_Flexibility.md) for detailed protocol flows, schema mappings, and message examples.
