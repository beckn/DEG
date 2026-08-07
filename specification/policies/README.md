# IES Policies – Rego Rules & Tests

The single source of truth for every policy in this repository. The `p2p-trading-ies-wave2` devkit mounts this directory into its containers (`/app/policies`); the demand-flex devkit still carries a local copy of its network policy.

## Files

| File | Purpose |
|------|---------|
| `p2p-trading-interdiscom.rego` | Policy rules (domain, version, order, catalog, test-ID consistency) |
| `p2p-trading-ies-wave2-contractpolicy.rego` | Wave2 **seller-discom policy**: buyer-discom allowlist (`violations` → NACK at select/init/confirm) + itemized settlement `revenue_flows` (wheeling, shortfall penalty, platform charge cap) |
| `p2p-trading-ies-wave2-networkpolicy.rego` | Wave2 network policy run by `opapolicychecker` (mounted into the wave2 devkit containers) |
| `demand-flex-networkpolicy.rego` / `demand-flex-contractpolicy.rego` / `demand-flex-pac-contractpolicy.rego` | Demand-flexibility network + contract policies |
| [`test/`](./test/) | OPA unit tests (`<policy>_test.rego`) for the policies above |
| [`discom-policy-guide/`](./discom-policy-guide/) | How a discom authors, versions, and publishes its own policy (checksum, release tag, DeDi record) |

Run each policy against its own test file (a whole-directory `opa test .` trips over cross-package helper name clashes):

```bash
cd specification/policies
opa test p2p-trading-ies-wave2-contractpolicy.rego test/p2p-trading-ies-wave2-contractpolicy_test.rego -v
```

## Two policy layers: network & contract

DEG enforces policy through **two** ONIX pipeline plugins with different scopes. Getting the split right gives every rule exactly one home.

| | **Network policy** — `opapolicychecker` | **Contract policy** — `contractpolicyenforcer` |
|---|---|---|
| Pipeline step | `checkPolicy` | `contractpolicyenforcer` |
| Who owns it | Network operator — **one policy per `networkId`** | The contracting parties — **referenced per contract** |
| How it's selected | Adapter config (`opa-network-policies.yaml`), same for all traffic | `…contractAttributes.policy.url` + `queryPath`, travels in the payload |
| Where it runs | **Every module** (BAP+BPP, caller+receiver), every action | Only the pipelines it is wired into |
| What it can do | **Gate only** — evaluate `violations`, NACK if non-empty | **Gate and inject** — NACK on `violations`, and/or write `revenue_flows` into the payload |
| Action scoping | **Inside the rego** (`input.context.action`) — no per-action config | Per-action **plugin config** (`actions` / `violationActions`) |
| Integrity | Operator-hosted file/bundle (optionally signed) | Fetched from URL/DeDi, **checksum-verified** against a registry record |
| Owns | Universal **structural well-formedness** (schema-plus) | **Settlement** + party-agreed economic terms |

Rule of thumb: a universal invariant every message on the network must satisfy (column locks, grid alignment, interval-id sequences, cardinality, required roles) belongs in the **network** policy — action-gated inside the rego. Anything that computes money or varies per agreement belongs in the **contract** policy. For a worked example of the split, compare the rule indexes in the headers of [`demand-flex-networkpolicy.rego`](./demand-flex-networkpolicy.rego) (structure, incl. section 5) and [`demand-flex-contractpolicy.rego`](./demand-flex-contractpolicy.rego) (settlement only).

### Configuring the network policy (`opapolicychecker`)

Wire the `checkPolicy` step in each module and point it at a config file:

```yaml
checkPolicy:
  id: opapolicychecker
  config:
    networkPolicyConfig: ./config/opa-network-policies.yaml   # required
    refreshInterval: "24h"                                    # recompile cadence
```

`opa-network-policies.yaml` maps each `networkId` (plus a `default` fallback) to one rego + query:

```yaml
networkPolicies:
  default:
    type: file                                                # file | bundle | dir | manifest
    location: ./policies/demand_flex_networkpolicy.rego
    query: data.deg.policy.demand_flex_network.violations
  nfh.global/testnet-deg:
    type: file
    location: ./policies/demand_flex_networkpolicy.rego
    query: data.deg.policy.demand_flex_network.violations
```

| Key | Meaning |
|---|---|
| `type` | `file` (single rego), `bundle` (signed `.tar.gz`), `dir` (folder), `manifest` (via manifest loader) |
| `location` | Path or URL to the policy |
| `query` | Rego query returning the violation set/array (empty ⇒ pass) |
| `verification.*` | Optional signature check for `bundle` type: `verification.enabled`, `verification.publicKeyLookupUrl`, `verification.signatureLocation`, `verification.algorithm` |

The plugin passes the **whole envelope** (including `context.action`) to the rego, so action scoping lives in the rule bodies — there is no per-action plugin config. A non-empty `query` result on **any** module NACKs the message, so the network policy is enforced bilaterally regardless of which side is honest.

> **Devkit copy & drift.** The `p2p-trading-ies-wave2` devkit mounts this `specification/policies/` directory into its containers. The **demand-flex** devkit instead bundles a local copy at `devkits/demand-flex/policies/demand_flex_networkpolicy.rego` (mounted at `/app/policies`). That copy MUST track the canonical here — regenerate it after any edit:
> ```bash
> ./specification/scripts/sync-network-policies.sh
> ```

### Configuring the contract policy (`contractpolicyenforcer`)

The policy reference travels in the payload:

```json
"contractAttributes": {
  "policy": { "url": "https://…/my-policy.rego", "queryPath": "data.deg.contracts.demand_flex" }
}
```

The step is wired per pipeline. **Injection and enforcement are independent**: a step activates when the action is in `actions` **or** `violationActions`.

| Key | Meaning | Default |
|---|---|---|
| `actions` | **Injection** actions — write the policy's `revenue_flows` to `outputPath`. `""` = never inject | `on_status` |
| `violationActions` | **Enforcement** actions — non-empty `violations` ⇒ 400 NACK (fail-closed). Need **not** be a subset of `actions` | *(empty)* |
| `outputPath` | Destination path for injected output. **Required iff `actions` is non-empty** | *(none)* |
| `outputMode` | `raw` (array at leaf) or `jsonld` (wrapped object). **Required iff `actions` is non-empty** | *(none)* |
| `outputType` / `outputContextURL` / `outputArrayKey` | `@type` / `@context` / array key for `jsonld` mode | `RevenueFlow` / — / `revenueFlows` |
| `entryDefaults` | JSON merged into newly-created array entries (e.g. `{"status":{"code":"SETTLED"}}`) | *(none)* |
| `allowedPolicyUrlPrefixes` | Allowlist the payload's `policy.url` must start with | *(all)* |
| `cacheTTL` | Compiled-policy cache TTL (minimum `24h`) | `24h` |
| `debugLogging` / `enabled` | Verbose logging / on-off | `false` / `true` |

Common wirings:

```yaml
# Enforce-only (receiver): NACK a malformed pre-settlement contract, inject nothing.
- id: contractpolicyenforcer
  config:
    actions: ""
    violationActions: "select,init,confirm"

# Inject-on-settlement (BPP caller): write revenue flows on on_status; don't NACK.
- id: contractpolicyenforcer
  config:
    actions: "on_status"
    violationActions: ""
    outputPath: "message.contract.consideration[id=auto-revenue-flows].considerationAttributes"
    outputMode: "jsonld"
```

Enforcement is **fail-closed** on `violationActions`: a missing `policy.url`, a disallowed prefix, or a fetch/compile/eval failure also NACKs, so enforcement cannot be bypassed by stripping the policy reference. Authoring a contract/settlement policy is covered in depth in [`discom-policy-guide/`](./discom-policy-guide/).

## Prerequisites

Install the [OPA CLI](https://www.openpolicyagent.org/docs/latest/#running-opa):

```bash
# macOS
brew install opa

# or download directly
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_darwin_arm64_static
chmod +x opa && sudo mv opa /usr/local/bin/
```

## Running the unit tests

```bash
cd specification/policies
opa test p2p-trading-interdiscom.rego test/p2p-trading-interdiscom_test.rego -v
```

Expected output:

```
data.deg.policy.test_t1_all_real_ids_pass: PASS
data.deg.policy.test_t1_all_test_ids_pass: PASS
data.deg.policy.test_t1_provider_test_buyer_real_fail: PASS
data.deg.policy.test_t1_buyer_test_provider_real_fail: PASS
data.deg.policy.test_t1_buyer_test_provider_real_fail_utility: PASS
data.deg.policy.test_t1_buyer_wrong_test_meter_fail: PASS
data.deg.policy.test_t1_mixed_buyer_utility_fail: PASS
PASS: 7/7
```

## Evaluating a real payload

Use `opa eval` with an input JSON file against the `violations` rule:

```bash
opa eval \
  -d p2p-trading-interdiscom.rego \
  --input /path/to/input.json \
  'data.deg.policy.violations'
```

An empty array (`[]`) means the payload passes all rules. Any strings in the array are violation messages.

To filter for a specific rule category (e.g. test-ID consistency):

```bash
opa eval \
  -d p2p-trading-interdiscom.rego \
  --input /path/to/input.json \
  '[v | data.deg.policy.violations[v]; startswith(v, "test consistency:")]'
```

Use `jq` to patch an existing example inline without editing files:

```bash
POLICY=p2p-trading-interdiscom.rego
EXAMPLE=../../examples/p2p-trading-interdiscom/v2/confirm-request.json

opa eval -d "$POLICY" \
  --input <(jq '
    .message.order["beckn:buyer"]["beckn:buyerAttributes"].meterId = "TEST_SELLER_METER" |
    .message.order["beckn:orderItems"][0]["beckn:orderItemAttributes"].providerAttributes.utilityId = "PVVNL"
  ' "$EXAMPLE") \
  'data.deg.policy.violations'
```

## Rule summary

### Common (all actions)
| Rule | Description |
|------|-------------|
| C1 | `context.domain` must be `beckn.one:deg:p2p-trading-interdiscom:2.0.0` |
| C2 | `context.version` must be `2.0.0` |

### Order validation (when `message.order` exists)
| Rule | Description |
|------|-------------|
| O1 | Delivery window start must be ≥ `minDeliveryLeadHours` after `context.timestamp` (default 4h) |
| O2 | Validity window end must be ≥ `minDeliveryLeadHours` before delivery start |
| O4 | Buyer `meterId` must be non-empty and differ from every provider `meterId` |
| O5 | Ordered `unitQuantity` must be ≥ 0 and < offer `applicableQuantity` |
| O6 | `priceCurrency` must be `INR` |
| O7 | Quantity `unitText` must be `kWh` |
| O8 | `utilityCustomerId` and `utilityId` must be non-empty on buyer and every provider |
| O9–O12 | `@type` and `@context` must match expected values for `EnergyCustomer`, `EnergyTradeOrder`, `EnergyTradeOffer`, `beckn:Order`, `beckn:Buyer`, `beckn:Fulfillment`, `beckn:Offer` |

### Test-ID consistency (T1)
If **any** party (buyer or any provider) uses a test identifier (`meterId` or `utilityId` starting with `TEST_`), **all** parties must use test identifiers:

| Field | Required value |
|-------|---------------|
| Buyer `meterId` | `TEST_METER_BUYER` |
| Buyer `utilityId` | `TEST_DISCOM_BUYER` |
| Provider `meterId` | must start with `TEST_` |
| Provider `utilityId` | must start with `TEST_` |

### Catalog publish (`catalog_publish` action)
| Rule | Description |
|------|-------------|
| P1–P2 | Production network items must use an approved DISCOM (`TPDDL`, `PVVNL`, `BRPL`) |
| P3–P10 | Non-production items must use `TEST_METER_SELLER` / `TEST_DISCOM_SELLER`; validity/delivery windows, currency, units, and `@type`/`@context` are validated |

## Configuration

`minDeliveryLeadHours` defaults to `4`. Override by passing a data file:

```bash
echo '{"config": {"minDeliveryLeadHours": 6}}' > /tmp/config.json

opa eval \
  -d p2p-trading-interdiscom.rego \
  -d /tmp/config.json \
  --input /path/to/input.json \
  'data.deg.policy.violations'
```
