# Fork changes

This is a fork of [beckn/DEG](https://github.com/beckn/DEG), taken at
upstream commit `54a5c7b`. It exists to prototype and verify fixes for
defects found in the demand flexibility devkit.

**Nothing here has been accepted upstream.** Treat this fork as a
proposal with working evidence, not as a release.

## How to see exactly what changed

From a clone of this fork:

    git remote add upstream https://github.com/beckn/DEG.git
    git fetch upstream main
    git diff upstream/main

The CI workflow runs the equivalent on every push, so the Actions log
always carries an up-to-date summary of how this fork differs.

## Conventions

Every edit to an upstream file carries an ID of the form `FC-nnn`, which
appears in three places: a row in the table below, a marked block in the
file itself, and the commit message. CI fails if an ID appears in the
code but not in this file.

A marked block in a `.rego` file looks like this:

    # --- FORK EDIT FC-001 (demand-flex-networkpolicy.rego) --------
    # Upstream  : what the code said before
    # Change    : what it says now
    # Rationale : why
    # Register  : FORK-CHANGES.md FC-001
    # -------------------------------------------------------------

The marker names its own file, because the same ID may touch several and
a block pasted into the wrong module will not compile.

Each change is developed on a branch named after its ID. Files added by
this fork carry no markers and are listed separately.

## The test applied to every network-layer rule

> Would this rule still be true for a product nobody has invented yet?

A network rule states a floor every message must clear. A rule that
states a ceiling — that a column set is complete, or that all arrays
correlate — defines a product, and belongs in that product's contract
policy. This test identified FC-001, and it caught a rule being wrongly
reintroduced while FC-001 was being written (see Known limits).

## Changes to upstream files

| ID | File | Change | Rationale | Status |
|----|------|--------|-----------|--------|
| FC-001 | `specification/policies/demand-flex-networkpolicy.rego`<br>`specification/policies/test/demand-flex-networkpolicy_test.rego` | Rule 5b requires `CAPACITY_REQUESTED` by presence instead of pinning the need column set exactly. Rule 5c removed. Stage legend and rule index updated. Two tests asserting the removed locks replaced with three covering presence and permitted extra columns. | An exact-set check asserts a column set is complete, which defines a product rather than testing coherence. The two locks rejected 11 of 12 bid-curve fixtures shipped in the same devkit, before they reached the bid-curve contract policy that implements the correct rules for that product. Price and penalty are product terms and move to the product that depends on them. Follows the P2P network policy, which uses presence checks throughout. | Applied on `fc-001-column-presence`. Verified: bid-curve rejections 11 → 3, all three now rule 3a; 15 of 15 curtailment fixtures unchanged; settlement unchanged at 436.25; unit tests 113 → 114. |
| FC-002 | `devkits/demand-flex/uc2-bid-curve-pac/examples/init-request.json`<br>`…/on-init-response.json`<br>`…/on-status-response-resource-telemetry.json` | Added a `commitmentAttributes` time series declaring `OFFER_PRICE` and `CAPACITY_OFFERED`, copied from `confirm-request.json` and sharing the same interval grid. | **A design decision, not only a fixture repair.** Rule 3a requires `CAPACITY_OFFERED` from `init` onward. These three fixtures declared no commitment block at all, so a discovered-price flow reached `init` without stating what was being offered — and the utility cannot assemble a draft contract at `on_init` from nothing. This moves bidding from `confirm` to `init`. JSON carries no comments, so this row is the only in-repo record of the reasoning. | Applied on `fc-002-bid-at-init` |
| FC-003 | `specification/policies/demand-flex-pac-contractpolicy.rego`<br>`specification/policies/test/demand-flex-pac-contractpolicy_test.rego` | New violation requiring `OFFER_PRICE` and `CAPACITY_OFFERED` to carry equal numbers of values in each market interval. | The bid curve is read positionally and nothing checked the arrays aligned. `_ask_at_cleared` indexes prices by a position found in powers, so a mismatch silently drops entries and the pay-as-clear audit compares against an incomplete set of asks. Placed in the contract policy, not the network policy: `CAPACITY_CLEARED` and `CLEARING_PRICE` are scalars alongside a multi-entry curve, so a blanket rule would reject valid payloads. Which columns pair is product knowledge. | Applied on `fc-003-bid-curve-alignment` |
| FC-004 | `specification/policies/demand-flex-contractpolicy.rego`<br>`specification/policies/test/demand-flex-contractpolicy_test.rego` | `revenue_flows` is now gated on the performance collection being complete, as well as on a settlement-eligible record. New violation S4 explains the refusal. Four tests added. | Performance records may be paginated for large cohorts and nothing read `pageInfo`. Both paginated fixtures declare `isLast: false` against a stated total of 12,000 meters, carry 2, and settle in full. A genuine partial page would produce a signed, understated settlement with nothing to flag it. Uses the existing mechanism for pre-settlement contracts: leave `revenue_flows` undefined so the enforcer injects nothing. | Applied on `fc-004-pagination-guard` |
| FC-005 | `specification/policies/demand-flex-pac-contractpolicy.rego`<br>`specification/policies/test/demand-flex-pac-contractpolicy_test.rego` | Introduced the internal/exported split for revenue flows. `_revenue_flows` is computed unconditionally and feeds the net-zero check; the exported `revenue_flows` is gated on a settlement-eligible performance record and a complete collection. New violation explains the refusal. Four tests added. | Two defects. Pagination was unguarded, as in FC-004. And unlike the posted-price policy, this one had no settlement-eligibility gate at all — it exported flows whenever the body resolved. The split follows `demand-flex-contractpolicy.rego`: the exported name instructs the enforcer, the internal name holds what was computed, and the consistency check needs the latter regardless. | Applied on `fc-005-pac-pagination-guard` |
| FC-006 | `specification/policies/demand-flex-networkpolicy.rego`<br>`specification/policies/test/demand-flex-networkpolicy_test.rego`<br>11 fixtures under `devkits/demand-flex/uc2-bid-curve-pac/examples/` | Rule 5b additionally requires `SHORTFALL_PENALTY` on the need. All bid-curve fixtures carrying a need gain the column at 0.5, matching the penalty rate already in their offer inputs. | An aggregator pricing flexibility is pricing a risk and cannot price downside it has not been told about. Unlike `PRICE`, both products need it: posted-price to compute, discovered-price as a bid input. Required rather than optional so "no penalty" (0) is distinguishable from "not stated yet" (absent). Required from catalogue, which also prevents late introduction. | Applied on `fc-006-shortfall-penalty-required` |
| FC-007 | `specification/policies/demand-flex-contractpolicy.rego`<br>`specification/policies/test/demand-flex-contractpolicy_test.rego` | New violation requiring a `PRICE` column on the need. Two tests added. | The policy reads `PRICE` per interval but never checked it was declared — safe only because the network policy's column lock guaranteed it, which FC-001 removed. The requirement cannot live at the network layer, because a discovered-price event carries no `PRICE` and its absence is how that event declares itself. It belongs to the product that settles against a posted rate. Takes effect from `select` onward, since the contract policy is never invoked at `catalog/publish`; publishing the price at catalogue is an implementation obligation. | Applied on `fc-007-posted-price-requires-price` |
| FC-008 | `specification/schema/DemandFlexNeed/v2.0/attributes.yaml`<br>`specification/schema/DemandFlexBuyOffer/v2.0/attributes.yaml`<br>`specification/policies/demand-flex-contractpolicy.rego`<br>`specification/policies/test/demand-flex-contractpolicy_test.rego` | New optional `direction` attribute on the need (`SHED` \| `ABSORB`, default `SHED`). `_meter_reduction` becomes `_meter_delta` with two bodies branching on it. New violation on an unrecognised value. Both schemas' negative-price claims removed. | The offer schema claimed a negative `PRICE` paid for increased consumption and gave that as the reason no direction field existed. No policy implemented it, and it is insufficient in principle: the settlement rule changes, not just the sign of the result. Direction is declared because, unlike procurement mode, no existing carrier declares it — a separate absorb policy would duplicate settlement arithmetic differing in one operator. | Applied on `fc-008-direction-declaration` |
| FC-009 | `.github/workflows/policy-checks.yml` | Adds core contract schema validation of all 27 demand-flex fixtures using `scripts/validate_schema.py`, and rewrites the settlement assertion to use `scripts/evaluate_demand_flex_settlement.py`, which now checks both per-slot figures and the net-zero line rather than a single total. | CI had only ever evaluated Rego against JSON. Both scripts ship with the repository, so this exercises the maintainers' tooling rather than a reimplementation, and the settlement evaluator reads the policy URL from the payload instead of hardcoding one. | Applied on `fc-009-schema-validation`. 27 of 27 fixtures validate; settlement reports 237.50 + 198.75 = 436.25, net-zero verified. |
| FC-010 | `scripts/requirements.txt` | Adds a version floor of 4.18 on `jsonschema` and lists `referencing` explicitly. | `validate_schema.py` imports `referencing`, which became a `jsonschema` dependency only at 4.18. `requirements.txt` set no floor, so on a machine with an older system `jsonschema` — including a stock GitHub Ubuntu runner, which ships 4.10.3 — pip reports the requirement already satisfied, installs nothing, and the script crashes at import with `ModuleNotFoundError: No module named 'referencing'`. Reproduced in CI before this fix. | Applied on `fc-010-requirements-floor` |

### Carried over from FC-001

Three bid-curve fixtures remain rejected after FC-001, all by rule 3a,
all for the same reason — no `CAPACITY_OFFERED` column is declared at
all:

- `uc2-bid-curve-pac/examples/init-request.json`
- `uc2-bid-curve-pac/examples/on-init-response.json`
- `uc2-bid-curve-pac/examples/on-status-response-resource-telemetry.json`

Rule 3a is correct and unchanged: an aggregator that reaches `init`
without stating what it is offering has offered nothing, and the utility
cannot assemble a draft contract at `on_init` from it. The fixtures are
the defect. Addressed as FC-002, which also moves bidding in a
discovered-price event from `confirm` to `init`.

### The discovered-price flow after FC-002

1. Utility publishes a need carrying capacity only — no posted price
2. Aggregator discovers it and sees there are no pricing terms
3. `select` / `on_select` returns firm non-price terms
4. Aggregator bids at `init` — capacity and price together
5. Utility echoes the bid in a draft contract at `on_init`
6. Aggregator commits at `confirm`
7. Utility clears or declines at `on_confirm`

The aggregator signs before knowing the clearing outcome. That is correct
auction behaviour — a withdrawable bid would be a free option. The
aggregator is protected by the pay-as-clear invariant already enforced in
`demand-flex-pac-contractpolicy.rego`: the clearing price must be at least
the cheapest ask whose paired capacity covers the cleared quantity, and the
bid curve travels in the same contract, so the arithmetic can be checked
against the aggregator's own signed bid.

Step 7 has no defined shape for a decline. Tracked separately.

## Files added by this fork

| Path | Purpose |
|------|---------|
| `.github/workflows/policy-checks.yml` | Runs both demand flexibility policies against every shipped fixture. `conformance` asserts what should be true; `known-defects` asserts the current state of documented defects, so it goes red when one is fixed. |
| `FORK-CHANGES.md` | This file. |

## Verified findings

Confirmed by running the policies with OPA, not by reading them.

**Settlement.** The shipped curtailment fixtures settle to 436.25 INR,
violations empty. The implementation guide states 525, a figure not
reachable from the terms the same guide gives.

**Column rules.** 11 of 12 bid-curve fixtures are rejected by the shared
network policy; 15 of 15 curtailment fixtures pass. Three rule families
fire: two comparing column sets with exact equality, and one requiring
the committed-capacity column at a fixed stage. Rejected messages never
reach the bid-curve contract policy, which implements the correct column
rules for that product.

**Pagination.** Both paginated fixtures declare `isLast: false` with a
stated total of 12,000 meters, carry 2 meters, and still settle to the
full 436.25. One is not even the first page.

## Known limits

**A rule withdrawn before it shipped.** A network rule requiring all
parallel `values` arrays within an interval to be equal length was
drafted and removed. A bid curve carries several tranches
(`OFFER_PRICE` and `CAPACITY_OFFERED`, four entries each) while its
clearing result is a scalar (`CLEARING_PRICE`, one entry), so differing
lengths in one interval are legitimate. Positional correspondence holds
between specific declared columns, which is product knowledge. Deferred
to the bid-curve contract policy.

**Commercial terms can be revised, not just added late.** Terms are
restated at `on_select`, `on_init` and `on_confirm`, each in a signed
message the counterparty retains, so a revision is non-repudiable and
visible before signing. Policy evaluation is stateless and cannot refuse
the revised message, so detection rests on the counterparty comparing
terms across messages. A digest of published terms carried in the
contract would make refusal automatic, as the bid-curve clearing audit
already does for clearing price. Not proposed for this version.

**Schema validation covers the contract envelope, not the domain
attributes.** FC-009 validates `message.contract` against the core Beckn
`Contract` structure for all 27 fixtures. It does not descend into
`resourceAttributes`, `commitmentAttributes` or `performanceAttributes`,
so `DemandFlexNeed`, `DemandFlexBuyOffer`, `DemandFlexPerformance` and
`BecknTimeSeries` are unchecked, and `additionalProperties: false` is
never exercised.

This matters for FC-008, which added a `direction` attribute to
`DemandFlexNeed`. Because that schema declares `additionalProperties:
false`, an undeclared field is a hard rejection on a real node — so the
edit is necessary for deployment and unverified by anything we run. No
fixture currently carries the attribute, so the gap is latent rather than
live. It closes when absorb fixtures are written, at which point a
focused check against the local `attributes.yaml` is needed.

Two fixtures receive no validation at all in either devkit:
`publish-catalog.json` and `discover-request.json`, neither of which
carries a `message.contract`.

## Related documents

Analysis supporting these changes is held outside this repository: a
register of deficiencies in the current devkit, and a draft
specification for an expanded one.

**Lost pages are undetectable.** FC-004 refuses to settle a page that
declares itself incomplete. It cannot detect that earlier pages of a
collection were lost — a final page arriving after two were dropped looks
complete to a stateless policy. Assembly is the receiver's
responsibility: collect by `collectionId`, verify the sequence, and only
then treat a settlement as final.
