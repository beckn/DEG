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
git checkout deg-prime-mvp

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

### 2. Import Postman collections (or Apidog)

Import the following collections into Postman from `postman/`:
- `demand-flex.BAP-DEG.postman_collection.json` (consumer/aggregator flows)
- `demand-flex.BPP-DEG.postman_collection.json` (utility flows)

Define the same variables as collection variables (or import [`apidog/demand-flex-local.postman_environment.json`](apidog/demand-flex-local.postman_environment.json) into Apidog / Postman). Names below match the Postman collection exactly.

| Variable | Typical value (Docker Compose on host) | Purpose |
|:---------|:---------------------------------------|:--------|
| `bap_adapter_url` | `http://localhost:8081/bap/caller` | Base URL for **BAP** outbound actions (`select`, `init`, …) |
| `bpp_adapter_url` | `http://localhost:8082/bpp/caller` | Base URL for **BPP** outbound actions (`publish`, `on_status`, …) |
| `bap_uri` | `http://onix-bap:8081/bap/receiver` | Inside JSON `context` — reachable from other containers |
| `bpp_uri` | `http://onix-bpp:8082/bpp/receiver` | Inside JSON `context` — reachable from other containers |
| `domain` | `beckn.one:deg:demand-flex:2.0.0` | `context.domain` |
| `version` | `2.0.0` | `context.version` |
| `bap_id` | `p2p-trading-sandbox1.com` | Matches `local-demand-flex-bap.yaml` keys |
| `bpp_id` | `p2p-trading-sandbox2.com` | Matches `local-demand-flex-bpp.yaml` keys |
| `transaction_id` | UUID (reuse across a flow) | Same value for steps 2–7 unless you intentionally split flows |
| `iso_date` | RFC3339 timestamp | Postman pre-request script sets this; set manually in Apidog |

All Beckn calls are **`POST`** with **`Content-Type: application/json`** unless noted.

### 3. Test the flow — API order (endpoints)

Run these **in order** on the adapters (what you click in Postman / Apidog). Paths are appended to `bap_adapter_url` or `bpp_adapter_url`.

| # | Collection | Folder → request name | Method | Endpoint (`{{var}}` / path) | Expanded example (default compose) | `context.action` in body | Notes |
|--:|:-----------|:------------------------|:------:|:-----------------------------|:-----------------------------------|:--------------------------|:------|
| 0 | — | (optional) adapter health | GET | `http://localhost:8081/health` and `http://localhost:8082/health` | Same | — | Confirms ONIX is up; not in Postman collections. |
| 1 | **demand-flex.BPP-DEG** | `publish` → **publish-catalog** | POST | `{{bpp_adapter_url}}/publish` | `http://localhost:8082/bpp/caller/publish` | `catalog/publish` | Utility publishes catalog (routes to configured catalog URL). Include `transactionId` in `context`. |
| 2 | **demand-flex.BAP-DEG** | `select` → **select-request** | POST | `{{bap_adapter_url}}/select` | `http://localhost:8081/bap/caller/select` | `select` | Forwards to sandbox BPP; sandbox **automatically** POSTs `on_select` back through ONIX to the BAP receiver — you do **not** need to run the BPP collection’s `on_select` request for this path. |
| 3 | **demand-flex.BAP-DEG** | `init` → **init-request** | POST | `{{bap_adapter_url}}/init` | `http://localhost:8081/bap/caller/init` | `init` | Triggers automatic **`on_init`** from sandbox BPP. |
| 4 | **demand-flex.BAP-DEG** | `confirm` → **confirm-request** | POST | `{{bap_adapter_url}}/confirm` | `http://localhost:8081/bap/caller/confirm` | `confirm` | Triggers automatic **`on_confirm`** from sandbox BPP. |
| 5 | **demand-flex.BAP-DEG** | `update` → **update-request-opt-in** | POST | `{{bap_adapter_url}}/update` | `http://localhost:8081/bap/caller/update` | `update` | Consumer / aggregator updates (e.g. participating meters). Sandbox BPP POSTs **`on_update`** after **update** (see `sandbox/bpp-response/on_update.json`). |
| 5b | **demand-flex.BAP-DEG** | `update` → **update-request-bdr-event-participation** | POST | `{{bap_adapter_url}}/update` | Same | `update` | BDR: **`energyEvents[]`** + **`energyEventParticipations[]`** (OPTED_IN). Same automatic **`on_update`** path. |
| 6 | **demand-flex.BPP-DEG** | `on_status` → **on-status-response-baselines** | POST | `{{bpp_adapter_url}}/on_status` | `http://localhost:8082/bpp/caller/on_status` | `on_status` | Utility-driven M&V: baselines (matches **`bdr-e2e/02`**). |
| 7 | **demand-flex.BPP-DEG** | `on_status` → **on-status-response-actuals** | POST | `{{bpp_adapter_url}}/on_status` | `http://localhost:8082/bpp/caller/on_status` | `on_status` | Actuals / delivery complete (**`bdr-e2e/03`**). |
| 8 | **demand-flex.BPP-DEG** | `on_status` → **on-status-response-settled** *(optional)* | POST | `{{bpp_adapter_url}}/on_status` | `http://localhost:8082/bpp/caller/on_status` | `on_status` | Settlement + **`revenueFlows`** (**`bdr-e2e/04`**). |

**Sandbox-only checks (not Beckn protocol):**

| # | Service | Method | URL | Notes |
|--:|:--------|:------:|:----|:------|
| — | sandbox-bap | GET | `http://localhost:3001/api/health` | Consumer mock |
| — | sandbox-bpp | GET | `http://localhost:3002/api/health` | Utility mock |

#### Requests in Postman but not in the default flow above

| Collection | Folder → request | Endpoint | Why skip in default compose |
|:-----------|:-------------------|:---------|:------------------------------|
| BAP | `discover` → discover-request | `{{bap_adapter_url}}/discover` | Routed to the CDS base URL in [`local-demand-flex-routing-BAP-Caller.yaml`](config/local-demand-flex-routing-BAP-Caller.yaml) (default matches p2p/ev-charging test CDS). **Beckn v2** [`Intent`](https://github.com/beckn/protocol-specifications-v2/blob/draft/api/v2.0.0/beckn.yaml) allows only `textSearch`, `filters`, `spatial`, and `mediaSearch` — do **not** use `descriptor` / `category` on `intent` (they fail `schemav2validator`). Example: [`examples/demand-flex/v2/discover-request.json`](../../examples/demand-flex/v2/discover-request.json). |
| BPP | `on_discover` → on-discover-response | `{{bpp_adapter_url}}/on_discover` | Only needed if you manually simulate a catalog callback; not part of the numbered publish → select → … flow. |
| BPP | `on_select` / `on_init` / `on_confirm` → *on-*-response* | `{{bpp_adapter_url}}/on_select`, `/on_init`, `/on_confirm` | Use when **manually** driving BPP → BAP callbacks **without** relying on sandbox-bpp automation (steps 2–4 already trigger those via the sandbox). |

**Method summary:** every Beckn adapter call uses **`POST {{bap_adapter_url}}/<action>`** or **`POST {{bpp_adapter_url}}/<action>`** where `<action>` is the path segment (`select`, `publish`, `on_status`, …), matching the Postman **raw** URL on each request.

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
| `bap_adapter_url` | `http://localhost:8081/bap/caller` | BAP Postman base (host → published port) |
| `bpp_adapter_url` | `http://localhost:8082/bpp/caller` | BPP Postman base |
| `bap_id` | `p2p-trading-sandbox1.com` | Matches `local-demand-flex-bap.yaml` / Postman |
| `bpp_id` | `p2p-trading-sandbox2.com` | Matches `local-demand-flex-bpp.yaml` / Postman |
| `bap_uri` | `http://onix-bap:8081/bap/receiver` | JSON `context` — Docker DNS |
| `bpp_uri` | `http://onix-bpp:8082/bpp/receiver` | JSON `context` — Docker DNS |

### Config Files

| File | Purpose |
|:-----|:--------|
| [`config/local-demand-flex-bap.yaml`](config/local-demand-flex-bap.yaml) | BAP adapter: registry, keys, schema validation, policy, routing |
| [`config/local-demand-flex-bpp.yaml`](config/local-demand-flex-bpp.yaml) | BPP adapter: same structure, BPP keys and routing |
| [`config/local-demand-flex-routing-*.yaml`](config/) | Routing tables for BAP/BPP receiver and caller modules |

### Beckn Protocol v2 transport

The adapters are configured for **Beckn Protocol API v2.0.0** ([OpenAPI `beckn.yaml`](https://raw.githubusercontent.com/beckn/protocol-specifications-v2/refs/heads/draft/api/v2.0.0/beckn.yaml)):

- **JSON bodies** in examples and sandboxes are the `context` + `message` payload only.
- **HTTP layer**: every request is expected to carry a Beckn **HTTP Signature** in the `Authorization` header; ONIX **receiver** modules run `validateSign`, **caller** modules run `sign` after schema and policy steps (see comments at the top of [`local-demand-flex-bap.yaml`](config/local-demand-flex-bap.yaml) and [`local-demand-flex-bpp.yaml`](config/local-demand-flex-bpp.yaml)).
- **Synchronous responses** follow the spec’s **Ack** shape (see the same OpenAPI and [`api/v2.0.0/README.md`](https://github.com/beckn/protocol-specifications-v2/blob/draft/api/v2.0.0/README.md) — “Security and acknowledgments”).

Postman raw bodies do not include headers; the adapter adds signing when traffic flows through `/bap/caller` or `/bpp/caller`.

### Policy Enforcement

This devkit uses the `opapolicychecker` plugin (new in onix-adapter 1.5.0) with the `checkPolicy` step:

```yaml
checkPolicy:
  id: opapolicychecker
  config:
    type: url
    location: "https://raw.githubusercontent.com/beckn/DEG/refs/heads/deg-prime-mvp/specification/policies/demand_flex_network.rego"
    query: "data.deg.policy.demand_flex_network.violations"
    refreshIntervalSeconds: "300"
```

The current policy is a **noop** (no violations). Replace the `location` URL with a real policy as network rules mature.

### Signing Keys

This devkit reuses the Ed25519 signing keys from the p2p-trading devkit. For production, generate fresh keys:

```bash
# Using Go (from beckn-signing-kit)
go run ./cmd/keygen
```

### Sandbox mock responses (BPP)

[`fidedocker/sandbox-2.0`](https://hub.docker.com/r/fidedocker/sandbox-2.0) is based on [beckn/sandbox](https://github.com/beckn/sandbox). For each incoming action (`select`, `init`, …) the BPP webhook loads a template from disk, merges it with the request `context`, then POSTs `on_*` to the adapter.

Layout inside the container (see [`src/utils/index.ts`](https://github.com/beckn/sandbox/blob/main/src/utils/index.ts)):

- Base: `/app/dist/webhook/jsons`
- Folder name: `normalizeDomain(context.domain)` — for `beckn.one:deg:demand-flex:2.0.0` this is `beckn.one:deg:demand-flex`
- With `PERSONA=bpp`: **`{domain}/response/bpp/on_select.json`**, **`on_init.json`**, **`on_confirm.json`**, **`on_status.json`**, **`on_update.json`**, **`on_cancel.json`**
- Template files should contain at least a **`message`** object; the sandbox overwrites **`context`** when sending the callback.
- **`on_status.json`** is generated from **BDR baselines** (`examples/demand-flex/v2/bdr-e2e/02-on-status-bdr-baselines.json`). **`on_update.json`** / **`on_cancel.json`** include **EnergyEvent** / participation and cancellation slots so BDR matches the Postman / `bdr-e2e` examples. Only one **`on_status`** template is loaded per callback; run the BPP Postman **`on_status`** requests (baselines / actuals / settled) manually to walk M&V → settlement.

This devkit **builds** `sandbox-bpp` from [`sandbox/Dockerfile.bpp`](sandbox/Dockerfile.bpp) and copies [`sandbox/bpp-response/`](sandbox/bpp-response/) into that path (avoids bind-mounting a directory whose name contains `:` on Windows).

To refresh templates from DEG examples:

```bash
cd testnet/demand-flex-devkit/sandbox
python3 generate-bpp-response-json.py
```

Then rebuild: `docker compose -f install/docker-compose-demand-flex.yml build sandbox-bpp` (from `demand-flex-devkit`).

Optional: set env var **`BPP_CALLBACK_ENDPOINT`** (see [`src/webhook/controller.ts`](https://github.com/beckn/sandbox/blob/main/src/webhook/controller.ts)) to override callback base URL instead of deriving it from **`context.bppUri`**.

## Schemas

Domain schemas are hosted on the `deg-prime-mvp` branch:

| Schema | Slot | Description |
|:-------|:-----|:------------|
| [DemandFlexNeed](../../specification/schema/DemandFlexNeed/v2.0/) | `resourceAttributes` | Direction, event window, capacity type, location |
| [DemandFlexBuyOffer](../../specification/schema/DemandFlexBuyOffer/v2.0/) | `offerAttributes` | Incentive, penalties, premiums, taker, policy ref |
| [DEGContract](../../specification/schema/DEGContract/v2.0/) | `contractAttributes` | Contract type identifier |
| [DemandFlexPerformance](../../specification/schema/DemandFlexPerformance/v2.0/) | `performanceAttributes` | M&V baselines and actuals per meter |

## Regenerating Postman Collections

The checked-in **`demand-flex.BAP-DEG`** / **`demand-flex.BPP-DEG`** collections are maintained with the patch + enrich scripts (routing parity, BDR payloads, saved responses):

```bash
# From repo root (DEG)
python3 scripts/patch_demand_flex_postman.py
python3 scripts/enrich_demand_flex_postman_responses.py
```

`enrich_demand_flex_postman_responses.py` adds **saved responses** on each request: synchronous **ACK**, plus **reference JSON** for async **`on_*`** callbacks and BDR **`on_status`** steps (see `examples/demand-flex/v2/bdr-e2e/`).

Alternatively, regenerate from example JSON only (no BDR patch layer):

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
# BDR end-to-end sequence (event → baselines → actuals → settlement)
python3 scripts/validate_schema.py examples/demand-flex/v2/bdr-e2e/*.json
```

See [`examples/demand-flex/v2/bdr-e2e/README.md`](../../examples/demand-flex/v2/bdr-e2e/README.md) for the full BDR narrative.

## Troubleshooting

| Issue | Solution |
|:------|:---------|
| Adapter fails to start | Check Redis is healthy: `docker logs redis` |
| Schema validation errors | Ensure schemas are pushed to `deg-prime-mvp` branch |
| Policy check fails | Verify the rego URL is accessible: `curl -sI <url>` |
| Port conflicts | Stop other devkits first, or modify port mappings in docker-compose |
| **`sandbox-bpp`: `TypeError: Invalid URL` / `input: 'undefined'`** | In [beckn/sandbox `getCallbackUrl`](https://github.com/beckn/sandbox/blob/main/src/webhook/controller.ts), unless **`BPP_CALLBACK_ENDPOINT`** is set, the callback URL is built from **`context.bppUri`** (also **`bpp_uri`** / **`bpp_url`**). It must be a valid absolute URL, e.g. `http://onix-bpp:8082/bpp/receiver`. Missing or unexpanded variables often show up as the literal string `undefined`. |
| **`sandbox-bpp`: `File not found: .../on_select.json`** | No template under `/app/dist/webhook/jsons/<domain>/response/bpp/`. Default **`fidedocker/sandbox-2.0`** has none for demand-flex; this devkit’s **built** `sandbox-bpp` image adds them (see **Sandbox mock responses** above). |
| **`{"message":"no Route matched with those values"}`** on discover | Almost always **Kong** (or similar) in front of the **CDS** URL: nothing matches `POST` to `…/beckn/discover` for your `Host` header. Point `local-demand-flex-routing-BAP-Caller.yaml` discover rule at a CDS that actually exposes discover (default sslip test CDS), or add/fix the route on your gateway. Not an ONIX schema error. |

## Implementation Guide

See the full [Demand Flexibility Implementation Guide](../../docs/implementation-guides/v2/Demand_Flexibility/Demand_Flexibility.md) for detailed protocol flows, schema mappings, and message examples.
