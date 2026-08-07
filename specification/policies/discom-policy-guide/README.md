# DISCOM Policy Guide

How a distribution company (discom) authors, tests, versions, and publishes
the policy that governs P2P energy trades involving its prosumers — and how
the network enforces it.

What's in this directory:

```
discom-policy-guide/
├── README.md                    ← you are here
├── example-discom-policy.rego   ← heavily commented template — copy this
├── validate-policy.sh           ← one-command validation of any policy
└── examples/                    ← minimal payloads, one per behavior
    ├── init-allowed.json                  → no violations, no injection
    ├── init-blocked-discom.json           → allowlist violation (NACK)
    ├── init-unknown-network.json          → network-membership violation (NACK)
    ├── init-prod-blocked-test-partner.json→ test-only partner on prod (NACK)
    ├── init-bad-ledger-url.json           → unrecognized discom ledger (NACK)
    ├── init-policy-not-applicable.json    → seller discom not covered (NACK)
    ├── init-wrong-currency.json           → non-INR pricing (NACK)
    ├── publish-allowed.json               → clean catalog publish, no violations
    ├── publish-blocked-provider.json      → catalog by uncovered discom (NACK)
    └── on-status-settled.json             → 4 itemized net-zero revenue flows
```

## Contents

1. [What a discom policy is](#1-what-a-discom-policy-is)
2. [How the network enforces it](#2-how-the-network-enforces-it)
3. [The interface your policy must export](#3-the-interface-your-policy-must-export)
4. [Author your policy](#4-author-your-policy)
5. [Test and validate](#5-test-and-validate)
6. [Best practices: action gating and cheap evaluation](#6-best-practices-action-gating-and-cheap-evaluation)
7. [Publish: checksum → release tag → stable URL → DeDi record](#7-publish-checksum--release-tag--stable-url--dedi-record)
8. [Checklist](#8-checklist)

## 1. What a discom policy is

A discom policy is a single [OPA rego](https://www.openpolicyagent.org/docs/latest/policy-language/)
artifact that declares, in one place:

- **Network membership** — which IES P2P trading networks (test and
  production) the discom recognizes. A trade arriving on any other
  `context.networkId` is rejected outright.
- **Applicability** — the discoms this policy applies to, declared upfront
  (several discoms may share one common policy). If the selling prosumer's
  discom is not one of them, the catalog publisher linked the wrong policy
  and the trade is rejected rather than judged under rules that don't
  govern it.
- **Settlement currency** — prices must be in a permitted currency (INR);
  anything else is rejected.
- **Ledger endpoints** — both discoms (`buyerDiscom` and `sellerDiscom`
  participants) must record the trade against a recognized ledger: in
  production, the canonical IES P2P energy ledger
  `https://ies-p2p-energy-ledger.beckn.io`.
- **Trading rules** — an allowlist of counterpart discoms whose customers may
  buy energy from this discom's prosumers, **per environment**: the test
  network's allowlist can include prospective partners the discom is not yet
  permitted to trade with under production regulations, so pilots can run
  before regulatory approval. Each environment has its own
  `enforce_allowlist` switch — set it to `false` and the allowlist is not
  merely unenforced for that environment but never even evaluated.
  Everything environment-specific lives in one `environments` map; the rules
  themselves are identical for test and production.
- **Charges** — the discom's wheeling charges, delivery-shortfall penalty
  rate, and the cap on what a trading platform may retain. These feed the
  settlement computation and appear itemized in every revenue flow.
- **Settlement computation** — how the trade value is split between the four
  roles (`buyerPlatform`, `sellerPlatform`, `buyerDiscom`, `sellerDiscom`) as
  a net-zero `revenue_flows` array.

Broken rules surface as `violations`, and violations get trades **NACKed**
before they form.

The catalog publisher links the **prosumer's discom's** policy into every
trade via `message.contract.contractAttributes.policy`:

```json
"policy": {
  "url": "https://api.dedi.global/dedi/lookup/indiaenergystack.in/ies-policies/<record-name>",
  "queryPath": "data.deg.contracts.p2p_trading"
}
```

So one policy — authored by the discom whose prosumer is selling — governs
each trade end to end.

## 2. How the network enforces it

The ONIX adapter's `contractpolicyenforcer` step resolves `policy.url` (verifying
its checksum against the DeDi record), compiles the rego, and evaluates it against
the full message. **Injection and enforcement are two independent switches**,
configured per pipeline in the adapter YAML — the step activates when the action
is in `actions` **or** `violationActions`:

| Config | Role | Behavior |
|---|---|---|
| `violationActions: "select,init,confirm"` (receiver) | **Enforce** trades | Non-empty `violations` → synchronous **400 NACK**; fail-closed (a missing / unfetchable / checksum-mismatched policy also NACKs) |
| `violationActions: "publish"` (caller; matches the compound `catalog/publish`) | **Enforce** publishes | Seller-side self-protection: every catalog offer's linked policy is evaluated (applicability, currency, network membership) and a violating catalog is NACKed **before it reaches the fabric** — catching a wrongly-linked policy at publish stops every downstream trade failing one by one |
| `actions: "on_status"` + `outputPath` | **Inject** settlement | Once settled intervals exist, `revenue_flows` is written into the payload at `outputPath`. Set `violationActions: ""` here so intermediate baseline / telemetry pushes are never NACKed |

`actions` selects the **injection** actions and requires `outputPath` / `outputMode`
when non-empty; `violationActions` selects the **enforcement** actions and needs
neither. They are independent — a step may enforce on `select,init,confirm` and
inject only on `on_status` (the two lists need not overlap). Full config-key
reference: [`../README.md` → Configuring the contract policy](../README.md#configuring-the-contract-policy-contractpolicyenforcer).

> **Structure vs settlement — pick the right layer.** This guide covers the
> **contract / settlement** policy: the economic terms a discom binds to a trade.
> Universal *structural* well-formedness (required roles, column locks, grid
> alignment, interval-id sequences) is the **network** policy's job
> (`opapolicychecker`) — action-gated inside that rego and run on every module.
> Keep your `violations` here scoped to settlement integrity and applicability;
> don't re-implement structural checks that the network policy already owns.

The policy is evaluated against **two message shapes** — trade contracts
(`message.contract`) and catalog publishes (`message.catalogs[].offers[]`).
The template handles both with shape-agnostic sets (see the "Shape-agnostic
sets" block in the example policy): buyer-specific rules are shape-gated so
they can never fire at publish, where no buyer exists yet.

See the wave2 sellerapp config
([`devkits/p2p-trading-ies-wave2/config/local-p2p-trading-sellerapp.yaml`](../../../devkits/p2p-trading-ies-wave2/config/local-p2p-trading-sellerapp.yaml))
for a working example of both.

## 3. The interface your policy must export

The `contractpolicyenforcer` step queries the package named by `policy.queryPath`
and reads two keys from the result:

| Rule | Type | Contract |
|---|---|---|
| `violations` | set of strings | Non-empty ⇒ the trade is blocked on enforced actions. Scope settlement-integrity checks to `input.context.action == "on_status"` so they can never block select/init/confirm. |
| `revenue_flows` | array of `{role, value, currency, description}` | Only export it once settled intervals exist (otherwise zero-value flows get injected into pre-settlement payloads). Values must sum to zero. |

Everything else (charge rates, helper rules) is internal to your policy —
but keeping the exported names from the [example policy](./example-discom-policy.rego)
makes your policy drop-in compatible with the wave2 tooling.

## 4. Author your policy

Copy [`example-discom-policy.rego`](./example-discom-policy.rego) — it is a
fully commented template. Everything a discom decides lives in the
**DISCOM PARAMETERS** block at the top; the rest is mechanics you should not
need to touch:

| Knob | Meaning |
|---|---|
| `environments` | **One map holding everything that differs between test and production.** Each entry declares: `network_ids` (the `context.networkId` values that select this environment — must be disjoint across entries; an unknown networkId is a violation → NACK), `applicable_seller_discoms` (the discoms this policy applies to, declared upfront — a trade whose *selling* prosumer belongs to any other discom is NACKed as "wrong policy linked"), `enforce_allowlist` (per-environment switch; `false` means the allowlist is never even evaluated for that environment's traffic — e.g. keep production enforced while opening the test network during an onboarding drive), `allowed_buyer_discoms` (per-environment counterpart allowlist — put a prospective partner in the **test** entry to pilot trades before the regulator approves them for **production**; include your own utilityId so intra-discom trades stay allowed), and `allowed_ledger_urls` (permitted `ledgerUrl` values for the buyerDiscom/sellerDiscom participants — production pins the canonical IES P2P energy ledger `https://ies-p2p-energy-ledger.beckn.io`; the test entry may add local/sandbox ledger endpoints). |
| `allowed_currencies` | Permitted settlement currency — `{"INR"}`. A payload pricing energy in any other currency is a violation → NACK. |
| `wheeling_charge_buyer_per_kwh` / `wheeling_charge_seller_per_kwh` | Wheeling charges, INR per settled kWh. Shared across environments — move them into the `environments` map (read via `_env`) if rates ever need to differ. |
| `penalty_rate_per_kwh` | Penalty on under-delivery (REQUESTED_QTY − FINAL_ALLOC, clamped ≥ 0), INR/kWh. |
| `platform_charge_cap_per_kwh` | Ceiling on what a trading platform may retain; disclosed in the settlement itemization. |

The design rule behind the map: **rules are environment-agnostic, data is
environment-specific** (see [6.3](#63-vary-data-per-environment-never-rules)).
Test and production always execute the same logic; only the `environments`
entry they resolve to differs.

Keep the package as `deg.contracts.p2p_trading` (then `policy.queryPath`
stays `data.deg.contracts.p2p_trading`), or rename both consistently.

> Naming gotcha: don't start rule names with `test_` (e.g. `test_network_ids`)
> — `opa test` treats `test_`-prefixed rules as unit tests. That's why the
> template uses `network_ids_test`.

## 5. Test and validate

### One command

```bash
cd specification/policies/discom-policy-guide
./validate-policy.sh my-discom-policy.rego
```

The script runs three stages: `opa check` (compiles), `opa test` (your unit
tests, if a `<policy>_test.rego` sits next to the policy), and a behavioral
suite that evaluates the policy against every payload in
[`examples/`](./examples/) and asserts the expected outcome:

| Payload | Scenario | Expected |
|---|---|---|
| `init-allowed.json` | Allowed buyer (`TEST_DISCOM_BUYER`), test network | `violations == []`, no `revenue_flows` (nothing to inject pre-settlement) |
| `init-blocked-discom.json` | Buyer discom not in the active allowlist | violation `"... not allowed to trade ..."` → NACK |
| `init-unknown-network.json` | `networkId` not in `network_ids_test`/`prod` | violation `"... not a recognized IES P2P trading network ..."` → NACK |
| `init-prod-blocked-test-partner.json` | Partner in the test allowlist arriving on the **production** network | violation `"... on the production network ..."` → NACK |
| `init-bad-ledger-url.json` | Discom participants recording against an unrecognized ledger endpoint | violation `"... not a permitted ledger endpoint ..."` → NACK |
| `init-policy-not-applicable.json` | Seller discom not in `applicable_seller_discoms` (wrong policy linked) | violation `"this policy does not apply to seller discom ..."` → NACK |
| `init-wrong-currency.json` | `PRICE_PER_KWH` priced in EUR | violation `"settlement currency \"EUR\" is not permitted ..."` → NACK |
| `publish-allowed.json` | Clean catalog publish (applicable provider, INR) | `violations == []`, nothing injected |
| `publish-blocked-provider.json` | Catalog offer from a discom this policy doesn't cover | violation `"this policy does not apply to seller discom ..."` → NACK at publish |
| `on-status-settled.json` | Settled interval (20 of 20.5 kWh @ 12.5 INR) | `violations == []`, 4 itemized flows, values sum to 0 |

Expected output:

```
[1/3] opa check ...
      OK
[2/3] opa test my-discom-policy.rego my-discom-policy_test.rego ...
PASS: 21/21
[3/3] behavioral suite against examples/*.json ...
      PASS  allowed init: no violations, no flows  (init-allowed.json)
      PASS  blocked discom: allowlist violation    (init-blocked-discom.json)
      PASS  unknown network: membership violation  (init-unknown-network.json)
      PASS  test-only partner blocked on prod      (init-prod-blocked-test-partner.json)
      PASS  settled: 4 itemized flows, net-zero    (on-status-settled.json)

All checks passed.
```

The example payloads are deliberately minimal — they contain exactly the
fields the policy reads, so they double as documentation of the input
contract. After editing your allowlists, adjust the buyer `utilityId` values
in your own copies of the payloads (or add payloads for your real partner
discoms).

### Unit tests

Write `with input as` tests per action, including the "must NOT fire here"
cases. The wave2 policy's test file
([`p2p-trading-ies-wave2-contractpolicy_test.rego`](../test/p2p-trading-ies-wave2-contractpolicy_test.rego))
is the reference pattern — it covers allowlist pass/fail per environment,
the `enforce_allowlist` switch (`with enforce_allowlist as false`), network
membership, charge math, shortfall penalty, and action scoping.

### Ad-hoc evaluation

```bash
opa eval -d my-discom-policy.rego \
  --input examples/init-allowed.json \
  'data.deg.contracts.p2p_trading.violations'
```

## 6. Best practices: action gating and cheap evaluation

Your policy runs inline in the message pipeline on every configured action —
badly scoped rules NACK legitimate traffic, and badly ordered rules burn
evaluation time on messages they were never meant to judge.

### 6.1 Gate every rule class by action — and put the guard FIRST

OPA evaluates a rule body top to bottom and abandons it at the first failing
expression. A guard on `input.context.action` as the **first** line means the
rest of the body — interval walks, aggregations, sprintf — is never evaluated
for other actions:

```rego
# GOOD — action guard first: for init/confirm this rule costs one comparison.
violations contains msg if {
	input.context.action == "on_status"      # cheapest, most selective first
	some i in _commit_ts.intervals            # only runs on on_status
	i.id in _settled_interval_ids
	not _price_by_id[i.id]
	msg := sprintf("settled interval %v has no matching PRICE_PER_KWH interval", [i.id])
}

# BAD — walks every interval on every action, then throws the work away.
violations contains msg if {
	some i in _commit_ts.intervals
	i.id in _settled_interval_ids
	not _price_by_id[i.id]
	input.context.action == "on_status"       # guard last = wasted evaluation
	msg := sprintf(...)
}
```

For rule classes that apply to several actions, name the gate once and reuse
it — this also documents intent:

```rego
_trade_formation_actions := {"select", "init", "confirm"}

_is_trade_formation if input.context.action in _trade_formation_actions
```

The same principle powers feature switches: `_env.enforce_allowlist` is the
first guard of every allowlist rule, so an environment with the switch off
doesn't just suppress the violation — it prevents the buyer-discom
extraction and set lookup from ever being demanded for its traffic.

### 6.2 Scope by lifecycle stage, not only by action

`on_status` arrives many times before settlement. Gating on the action alone
still fires settlement checks against half-built contracts. Add a data-shape
gate (here: "settled intervals exist") so the rule only judges messages that
carry the data it validates:

```rego
_settled := count(_settled_interval_ids) > 0

violations contains msg if {
	input.context.action == "on_status"
	_settled                                  # stage gate: skip pre-settlement on_status
	not net_zero_ok
	msg := sprintf("net-zero failed: revenue sum = %g (expected 0)", [_revenue_sum])
}
```

The same idea protects injection: export `revenue_flows` only when there is
something to inject, so trade-formation payloads stay untouched:

```rego
revenue_flows := [...] if _settled
```

### 6.3 Vary data per environment, never rules

Test and production must stay maintainable as one policy: if each
environment gets its own copy of a rule, every future change has to be made
twice and the copies drift. Instead, keep **one map of environment data** and
make every rule read its settings through the resolved entry:

```rego
environments := {
	"test":       {"network_ids": {...}, "enforce_allowlist": true, "allowed_buyer_discoms": {...}},
	"production": {"network_ids": {...}, "enforce_allowlist": true, "allowed_buyer_discoms": {...}},
}

# Resolution — the ONLY place environments are told apart.
_environment := name if {
	some name, env in environments
	_network_id in env.network_ids
}

_env := environments[_environment]

# One allowlist rule for every environment; it never mentions test or prod.
violations contains msg if {
	_env.enforce_allowlist
	_buyer_discom_id
	not _buyer_discom_id in _env.allowed_buyer_discoms
	msg := sprintf("buyer discom %q is not allowed ... on the %s network", [_buyer_discom_id, _environment])
}
```

What this buys you:

- **Symmetry for free** — enforcement, messages, and edge-case handling are
  identical in both environments because they are literally the same rule.
- **Safe by construction on unknown networks** — an unrecognized networkId
  resolves no entry, `_env` stays undefined, and every `_env`-reading rule
  simply cannot fire; the unconditional membership violation reports the
  problem. No rule can accidentally judge test traffic against production
  data or vice versa.
- **Cheap environment changes** — flipping `enforce_allowlist` for one
  environment, adding a partner to one allowlist, or adding a whole new
  environment (a staging network, a second testnet) is a data edit, not a
  logic change.
- **Testability** — unit tests exercise one environment's behavior by
  patching the map, not by mocking rules:

  ```rego
  _envs_test_allowlist_off := json.patch(environments, [{
  	"op": "replace", "path": "/test/enforce_allowlist", "value": false,
  }])

  test_allowlist_disabled_lets_outsider_through if {
  	count(violations) == 0 with input as inp with environments as _envs_test_allowlist_off
  }
  ```

Keep the `network_ids` sets disjoint across entries — a networkId in two
environments would make `_environment` ambiguous (a rego conflict error at
evaluation time). If a shared value (say a wheeling rate) one day needs to
differ per environment, move it *into* the map and read it via `_env` —
don't fork the rule that uses it.

### 6.4 Lean on OPA's laziness — rules are computed on demand and memoized

A complete rule (`trade_value := ...`) is **not** evaluated unless something
in the query actually needs it, and once evaluated its result is **cached for
the rest of that evaluation**. Two consequences:

- Expensive aggregates are free on actions whose rules never reference them —
  *provided* the referencing rules are action-gated (6.1). With the guard
  first, `trade_value` is simply never demanded at init. Same for
  environment resolution: with `_env.enforce_allowlist` guarding the
  allowlist rules, nothing environment-related is computed for actions where
  those rules don't run.
- Factor repeated expressions into named rules, not repeated inline logic:
  `total_settled_kwh` referenced by four flow descriptions is computed once,
  not four times.

**Caveat:** user-defined *functions* (`f(x) := ...`) are re-evaluated on every
call — they are not memoized. Use functions for per-item logic inside
comprehensions; use complete rules for shared scalars/aggregates.

### 6.5 Make undefined a non-event, not an error

Partial-set rules (`violations contains msg if {...}`) are undefined-safe: a
body that fails just contributes nothing. For scalars that other rules read,
declare a `default` so downstream arithmetic never hits undefined:

```rego
default penalty_charge := 0
penalty_charge := _round2(penalty_rate_per_kwh * total_shortfall_kwh) if _settled
```

And when a violation *should* fire on missing data (fail-closed decisions
like the allowlist), make that an explicit paired rule rather than an
accident of undefinedness:

```rego
violations contains msg if {
	_env.enforce_allowlist
	_buyer_discom_id                          # defined → check the allowlist
	not _buyer_discom_id in _env.allowed_buyer_discoms
	msg := sprintf("buyer discom %q is not allowed ...", [_buyer_discom_id])
}

violations contains msg if {
	_env.enforce_allowlist
	not _buyer_discom_id                      # undefined → its own, explicit violation
	msg := "cannot determine buyer discom: ..."
}
```

Only do this for data the decision genuinely requires — don't fail-closed on
optional fields that legitimately appear later in the lifecycle.

The environment resolution uses the same idea defensively: an unknown
networkId leaves `_env` undefined, so environment-dependent rules cannot
accidentally judge against the wrong environment's settings — the (cheap,
unconditional) network-membership violation fires instead.

### 6.6 Keep the exported surface stable and the rest private

The network contract is `violations` + `revenue_flows` (+ the documented
knobs). Prefix everything else with `_` so consumers and tests never couple
to internals, and future refactors can't break payloads.

### 6.7 Test each action's cost and behavior separately

Write `with input as` tests per action — including the "rule must NOT fire
here" cases (e.g. no FINAL_ALLOC violation at init). To find rules that
evaluate where they shouldn't, profile a representative payload per action:

```bash
opa eval -d my-discom-policy.rego --input examples/init-allowed.json \
  --profile --format=pretty 'data.deg.contracts.p2p_trading'
```

If an interval-walking rule shows up in the init profile, its action guard is
missing or not first.

## 7. Publish: checksum → release tag → stable URL → DeDi record

### 7.1 Compute the checksum

The DeDi record carries an integrity checksum of the exact bytes served at
your hosting URL:

```bash
shasum -a 256 my-discom-policy.rego
# → 3f6c1a…9be2  my-discom-policy.rego
```

That hex digest goes into the record's `data_url_checksum`, with
`data_url_checksum_type: sha256`. The `contractpolicyenforcer` step recomputes the
hash on every fetch and rejects the policy on mismatch — so the checksum, not
the hosting location, is what consumers trust.

### 7.2 Tag a release for a stable URL

The URL in the DeDi record must serve **immutable** content — if the file
changes under the same URL, every adapter's checksum verification breaks.
Never point a record at a branch URL for production use. Tag a release and
use the tag-pinned raw URL:

```bash
git add my-discom-policy.rego
git commit -m "policy: my-discom trading policy v1.0.0"
git tag policy-v1.0.0
git push origin main --tags
```

Stable URL form (GitHub):

```
https://raw.githubusercontent.com/<org>/<repo>/refs/tags/policy-v1.0.0/path/to/my-discom-policy.rego
```

To change the policy, publish a **new** tag and a **new** DeDi record version
(or a new record) — never rewrite a tag.

### 7.3 Host it anywhere — reference it in DeDi

The policy file itself can be hosted **anywhere**: the discom's own website,
the discom's git repo, an object store. Hosting is not what makes it
authoritative — the **DeDi record referencing it** is. A DeDi public-dataset
record binds a versioned, checksummed pointer to your artifact, and that
record URL is what payloads carry in `contractAttributes.policy.url`.

Create the record (via the [DeDi dashboard](https://dedi.global)) with these
fields (this is the live wave2 record as a template):

```jsonc
{
  "record_name": "acme-discom-trading-policy-v1",   // versioned name
  "description": "ACME Discom P2P trading policy (allowlist + charges + settlement)",
  "details": {
    "name": "acme-discom-trading-policy",
    "tags": ["p2p-trading", "policy", "settlement", "discom"],
    "type": "other",
    "publisher_id": "acme-discom.example.com",
    "data_url": "https://raw.githubusercontent.com/acme-discom/policies/refs/tags/policy-v1.0.0/my-discom-policy.rego",
    "data_url_checksum": "<sha256 hex from step 7.1>",
    "data_url_checksum_type": "sha256"
  }
}
```

The record is then resolvable at
`https://api.dedi.global/dedi/lookup/<namespace>/<registry>/<record_name>` —
that lookup URL is what goes into the payload's `policy.url`.

### 7.4 Publish under the IES namespace (recommended)

Publish your record in the **India Energy Stack** namespace/registry —
`indiaenergystack.in` / `ies-policies` — rather than a private namespace:

- **Uniform quality control**: IES reviews records entering `ies-policies`,
  so consumers get a consistent bar for policy quality and metadata.
- **A single root of trust**: adapters pin the namespace once via the
  `contractpolicyenforcer` step's `allowedPolicyUrlPrefixes` config and thereby
  accept any discom's policy published under it — no per-discom
  configuration:

  ```yaml
  - id: contractpolicyenforcer
    config:
      # Only India Energy Stack policy records on DeDi are accepted.
      allowedPolicyUrlPrefixes: "https://api.dedi.global/dedi/lookup/indiaenergystack.in"
  ```

A policy referenced from outside the allowlisted prefixes is rejected — on
enforced actions (select/init/confirm) that rejection is itself a NACK.

## 8. Checklist

- [ ] All edits confined to the DISCOM PARAMETERS section (everything below it is shared mechanics)
- [ ] `environments` map edited: `network_ids`, `applicable_seller_discoms`, per-environment `enforce_allowlist`, `allowed_buyer_discoms`, `allowed_ledger_urls`; currency + charge rates set
- [ ] Production `allowed_ledger_urls` pins the canonical IES ledger (`https://ies-p2p-energy-ledger.beckn.io`)
- [ ] `applicable_seller_discoms` lists every discom sharing this policy
- [ ] `network_ids` sets disjoint across environments
- [ ] Own utilityId present in every environment's allowlist (intra-discom trades allowed)
- [ ] Prospective (not-yet-regulated) partners only in the **test** environment's allowlist
- [ ] No environment-specific rule forks — rules read settings via `_env` only
- [ ] No shape-specific rule forks — shared facts collected via shape-agnostic sets; buyer/roles rules shape-gated so a clean catalog publish yields zero violations
- [ ] `./validate-policy.sh my-discom-policy.rego` — all checks pass
- [ ] Unit tests next to the policy (`<policy>_test.rego`), `opa test` green
- [ ] Every rule class action-gated, guard as the first body expression
- [ ] Settlement-integrity violations scoped to `on_status` + a stage gate
- [ ] `opa eval --profile` on an init payload shows no settlement rules evaluating
- [ ] sha256 computed from the exact hosted bytes
- [ ] Release tagged; `data_url` is tag-pinned (immutable), not a branch URL
- [ ] DeDi record created (IES namespace recommended), lookup URL resolves
- [ ] `policy.url` in the catalog/trade payloads points at the DeDi record
