# DEG Contract-as-Code Specification

**Version:** 0.1.0-draft
**Status:** Proposal
**Scope:** Generalized contract model for Digital Energy Grid (DEG) use cases

---

## 1. Problem Statement

Today, EV Charging, P2P Energy Trading, and Demand Flexibility each have separate schemas with duplicated concepts:

| Concept | EV Charging | P2P Trading | Demand Flexibility |
|---------|------------|-------------|-------------------|
| **What** is traded | kWh of charge | kWh of energy | Load curtailment/shift |
| **Who** participates | EV driver + CPO | Prosumer + Consumer + Utility | Aggregator + Consumer + Grid Operator |
| **How** fulfilled | Physical charging session | Grid injection + meter reading | Signal-driven load adjustment |
| **Terms** | Price/kWh, connector type | Price/kWh, delivery window, deviation penalty | Baseline, trigger signal, incentive |

Yet the **transactional structure** is identical: parties discover each other, negotiate terms, commit to obligations, fulfill them, and settle. A generalized "contract" model captures this.

---

## 2. Core Idea: Energy Contract as a Partially-Filled Template

An **Energy Contract** is a structured agreement between N roles, published as a partially-filled template on a Beckn catalog. Each role has:

- **Inputs** it must provide (parameters, credentials, signals)
- **Obligations** it must fulfill (deliver energy, curtail load, pay)
- **Conditions** under which obligations activate or change (time windows, grid signals, thresholds)

The contract progresses through Beckn's transaction lifecycle:

```
Template (Catalog/Offer)  →  Negotiated (Select)  →  Committed (Confirm)  →  Active (Fulfillment)  →  Settled (Post)
     ↑                            ↑                        ↑                       ↑
  Provider fills             Consumer fills            Both sign             Signals/meters
  their role inputs          their role inputs          off                  drive execution
```

---

## 3. Contract Structure

### 3.1 DEGContract Schema (Minimal)

```yaml
DEGContract:
  type: object
  required: [contractType, version, roles, terms]
  properties:

    contractType:
      type: string
      enum: [EV_CHARGING, P2P_ENERGY_TRADE, DEMAND_FLEXIBILITY, COMPOSITE]
      description: Primary contract classification. COMPOSITE for multi-use-case contracts.

    version:
      type: string
      pattern: '^\d+\.\d+\.\d+$'
      description: Semantic version of this contract template.

    roles:
      type: array
      minItems: 2
      items:
        $ref: '#/DEGRole'
      description: Participating roles with their required inputs and obligations.

    terms:
      type: array
      items:
        $ref: '#/DEGTerm'
      description: Contract terms — each is a named condition-obligation pair.

    energySpec:
      $ref: '#/EnergySpecification'
      description: What energy product is being contracted.

    fulfillmentSpec:
      $ref: '#/FulfillmentSpecification'
      description: How the contract is physically fulfilled.

    settlementSpec:
      $ref: '#/SettlementSpecification'
      description: How the contract is financially settled.
```

### 3.2 DEGRole

```yaml
DEGRole:
  type: object
  required: [roleId, roleType, inputs]
  properties:

    roleId:
      type: string
      description: Unique role identifier within this contract.
      example: "seller"

    roleType:
      type: string
      enum: [PRODUCER, CONSUMER, AGGREGATOR, GRID_OPERATOR, CPO, UTILITY, PROSUMER]
      description: Functional role classification.

    party:
      type: object
      description: >
        Filled when a party accepts this role. Maps to Beckn Provider or Buyer.
        Empty in template = open for acceptance.
      properties:
        partyId: { type: string }
        partyType: { type: string, enum: [PROVIDER, BUYER] }
        platformId: { type: string, description: "BAP or BPP subscriber ID" }
        attributes:
          $ref: 'core/v2/attributes.yaml#/components/schemas/Attributes'
          description: "Role-specific attributes (EnergyCustomer, etc.)"

    inputs:
      type: array
      items:
        $ref: '#/RoleInput'
      description: >
        Parameters this role must supply. Some filled by template author,
        others filled by accepting party. Unfilled inputs = open slots.

    obligations:
      type: array
      items:
        type: string
        description: References to DEGTerm.termId where this role has an obligation.
```

### 3.3 RoleInput

```yaml
RoleInput:
  type: object
  required: [inputId, inputType, required]
  properties:

    inputId:
      type: string
      description: Unique input identifier.
      example: "source_meter_id"

    inputType:
      type: string
      enum: [PARAMETER, ITEM_REF, CREDENTIAL, SIGNAL, METER_ID, LOCATION]
      description: Classification of this input.

    required:
      type: boolean
      default: true

    description:
      type: string

    schema:
      type: object
      description: JSON Schema for validating the input value.

    value:
      description: >
        The actual value. null/absent = unfilled slot (to be provided by accepting party).
      # any type

    filledBy:
      type: string
      description: roleId of the party that fills this input. If absent, filled by the role owner.

    providedAt:
      type: string
      enum: [TEMPLATE, NEGOTIATION, COMMITMENT, FULFILLMENT]
      description: When in the lifecycle this input must be provided.
```

### 3.4 DEGTerm (Condition-Obligation Pairs)

This is where Rego/OPA-style policy logic enters. Each term defines:
- **When** it activates (condition)
- **What** must happen (obligation)
- **What if** it's violated (consequence)

```yaml
DEGTerm:
  type: object
  required: [termId, termType, condition, obligation]
  properties:

    termId:
      type: string
      example: "delivery_obligation"

    termType:
      type: string
      enum: [DELIVERY, PAYMENT, SIGNAL_RESPONSE, QUALITY, DEVIATION_PENALTY, CANCELLATION]

    condition:
      $ref: '#/PolicyExpression'
      description: >
        When this term activates. Expressed as a declarative rule.
        Evaluated against contract state + external signals.

    obligation:
      $ref: '#/PolicyExpression'
      description: What must be true for this term to be satisfied.

    consequence:
      $ref: '#/PolicyExpression'
      description: What happens if the obligation is violated (penalty, cancellation, etc.)

    appliesTo:
      type: array
      items: { type: string }
      description: roleIds this term applies to.
```

### 3.5 PolicyExpression (Rego-Inspired)

Rather than embedding a full Rego runtime, we define a declarative expression format inspired by OPA's data model. The key insight from OPA:

- **Input**: the transaction/event being evaluated (a Beckn message, meter reading, grid signal)
- **Data**: reference data (contract terms, thresholds, rate cards)
- **Output**: a decision (compliant/violated, calculated price, triggered action)

```yaml
PolicyExpression:
  type: object
  description: >
    Declarative condition/rule. Can be simple (field comparison) or
    reference an external policy (Rego file, Arazzo workflow step).
  properties:

    # Simple inline expression
    expr:
      type: string
      description: >
        JSONPath-like expression over contract state.
        Examples:
          "deliveredQuantity >= terms.minQuantity"
          "currentTime within deliveryWindow"
          "gridFrequency < 49.5"
      example: "deliveredQuantity >= 10.0 AND deliveredQuantity <= 50.0"

    # Structured rule (for more complex conditions)
    rule:
      type: object
      properties:
        operator:
          type: string
          enum: [AND, OR, NOT, GTE, LTE, EQ, NEQ, WITHIN, BETWEEN, IF_THEN]
        operands:
          type: array
          items:
            oneOf:
              - $ref: '#/PolicyExpression'
              - type: object
                properties:
                  field: { type: string }
                  value: {}

    # External policy reference (for complex logic)
    policyRef:
      type: object
      properties:
        type:
          type: string
          enum: [REGO, ARAZZO, WEBHOOK]
        uri:
          type: string
          format: uri
          description: URI to the policy file or endpoint.
        package:
          type: string
          description: For Rego — the package path (e.g., "deg.contracts.ev_charging")
        entrypoint:
          type: string
          description: For Rego — the rule to evaluate (e.g., "delivery_compliant")
```

### 3.6 EnergySpecification

```yaml
EnergySpecification:
  type: object
  description: What energy product is being contracted.
  properties:

    energyType:
      type: string
      enum: [ELECTRICAL, THERMAL, GAS]

    sourceType:
      type: string
      enum: [SOLAR, WIND, HYDRO, GRID, BATTERY, ANY]

    quantity:
      $ref: 'core/v2/attributes.yaml#/components/schemas/Quantity'

    qualityConstraints:
      type: object
      properties:
        greenCertRequired: { type: boolean }
        maxCarbonIntensity: { type: number, description: "gCO2/kWh" }
        powerFactor: { type: number, minimum: 0, maximum: 1 }
```

### 3.7 FulfillmentSpecification

```yaml
FulfillmentSpecification:
  type: object
  properties:

    deliveryMode:
      type: string
      enum: [EV_CHARGING, BATTERY_SWAP, GRID_INJECTION, V2G, LOAD_CURTAILMENT, LOAD_SHIFT, VIRTUAL]

    deliveryWindow:
      $ref: 'core/v2/attributes.yaml#/components/schemas/TimePeriod'

    location:
      $ref: 'core/v2/attributes.yaml#/components/schemas/Location'

    meterIds:
      type: array
      items: { type: string }
      description: Meter identifiers for measuring fulfillment.

    signals:
      type: array
      items:
        type: object
        properties:
          signalType: { type: string, enum: [GRID_FREQUENCY, PRICE_SIGNAL, CURTAILMENT_COMMAND, START_STOP] }
          source: { type: string, description: "URI of signal source" }
          protocol: { type: string, enum: [MQTT, HTTP_WEBHOOK, OCPP, OPENADR] }
      description: Real-time signals used during fulfillment.
```

### 3.8 RevenueModel (Multi-Party Net-Zero Flows)

Every energy contract involves money moving between roles. The **RevenueModel** makes this explicit with two invariants:

1. **Net-zero**: The sum of all flows across all roles = 0 (money is conserved)
2. **Per-role legibility**: Any agent acting on behalf of a role can compute its net position by filtering flows where it is `from` or `to`

```yaml
RevenueModel:
  type: object
  required: [flows]
  description: >
    Declares all monetary flows between roles. The sum of all flow amounts
    MUST equal zero at settlement (net-zero invariant). Each flow has a
    formula that computes its value from contract state.
  properties:

    flows:
      type: array
      minItems: 1
      items:
        $ref: '#/RevenueFlow'
      description: >
        Directed monetary flows. Positive amount = transfer from → to.
        The sum of all flow amounts must be zero.

    netZeroCheck:
      $ref: '#/PolicyExpression'
      description: >
        Optional Rego/expr that validates the net-zero invariant.
        Default: "sum(flows[].computedAmount) == 0"

RevenueFlow:
  type: object
  required: [flowId, from, to, flowType, formula]
  properties:

    flowId:
      type: string
      description: Unique flow identifier.
      example: "energy_payment"

    from:
      type: string
      description: roleId of the paying party.

    to:
      type: string
      description: roleId of the receiving party.

    flowType:
      type: string
      enum: [ENERGY_PAYMENT, WHEELING_CHARGE, PLATFORM_FEE, INCENTIVE,
             DEVIATION_PENALTY, CANCELLATION_FEE, TAX, CREDIT, ESCROW_RELEASE]
      description: Classification of the monetary flow.

    formula:
      $ref: '#/PolicyExpression'
      description: >
        Expression that computes the flow amount from contract state.
        Examples:
          "deliveredKwh * pricePerKwh"
          "totalPayment * 0.02"  (2% platform fee)
          "shortfall * deviationPenaltyPerKwh"

    currency:
      type: string
      default: "INR"

    computedAmount:
      type: number
      description: >
        Filled at settlement time. The evaluated result of the formula.
        Positive = transfer in the from→to direction.

    triggeredBy:
      type: string
      description: >
        termId that triggers this flow. Links revenue to contract terms.
```

#### How an Agent Reads Its Revenue Position

Any agent acting for roleId `R` computes:

```
netPosition(R) = sum(flow.computedAmount for flow where flow.to == R)
               - sum(flow.computedAmount for flow where flow.from == R)
```

- **Positive** net = role R **receives** money (revenue)
- **Negative** net = role R **pays** money (cost)
- **Sum of all netPosition across all roles = 0** (the invariant)

#### Example: P2P Trade Revenue Model

```yaml
revenueModel:
  flows:
    - flowId: energy_payment
      from: buyer
      to: seller
      flowType: ENERGY_PAYMENT
      formula:
        expr: "deliveredKwh * pricePerKwh"
      triggeredBy: pricing

    - flowId: wheeling_charge
      from: buyer
      to: utility
      flowType: WHEELING_CHARGE
      formula:
        expr: "deliveredKwh * wheelingRatePerKwh"
      triggeredBy: utility_registration

    - flowId: platform_fee_buyer
      from: buyer
      to: platform
      flowType: PLATFORM_FEE
      formula:
        expr: "energyPayment * 0.01"       # 1% from buyer side

    - flowId: platform_fee_seller
      from: seller
      to: platform
      flowType: PLATFORM_FEE
      formula:
        expr: "energyPayment * 0.01"       # 1% from seller side

    - flowId: deviation_penalty
      from: seller
      to: buyer
      flowType: DEVIATION_PENALTY
      formula:
        policyRef:
          type: REGO
          package: "deg.contracts.p2p_trade"
          entrypoint: "deviation_penalty"
      triggeredBy: delivery_obligation
```

**Per-role view (at settlement with 10 kWh @ INR 4.50/kWh, 0.50 wheeling, no deviation):**

| Role | Inflows | Outflows | Net Position |
|------|---------|----------|-------------|
| **buyer** | - | 45.00 (energy) + 5.00 (wheeling) + 0.45 (fee) = **50.45** | **-50.45** (pays) |
| **seller** | 45.00 (energy) | 0.45 (fee) = **0.45** | **+44.55** (earns) |
| **utility** | 5.00 (wheeling) | - | **+5.00** (earns) |
| **platform** | 0.45 + 0.45 = 0.90 | - | **+0.90** (earns) |
| **Total** | | | **0.00** |

#### Example: Demand Flexibility Revenue Model

```yaml
revenueModel:
  flows:
    - flowId: grid_savings
      from: grid_operator
      to: aggregator
      flowType: ENERGY_PAYMENT
      formula:
        expr: "totalCurtailmentKwh * gridSavingsRatePerKwh"

    - flowId: participant_incentive
      from: aggregator
      to: participant
      flowType: INCENTIVE
      formula:
        expr: "participantCurtailmentKwh * incentiveRate * eventDurationHours"
      triggeredBy: incentive_payment

    - flowId: aggregator_margin
      from: aggregator
      to: aggregator
      flowType: PLATFORM_FEE
      formula:
        expr: "gridSavings - participantIncentive"  # implicit: aggregator keeps the spread
      # Note: this is a self-loop that represents retained margin
      # An alternative is to simply not model it, and let
      # netPosition(aggregator) = gridSavings - incentives naturally.
```

**Per-role view (100 kWh curtailed, grid saves INR 8/kWh, incentive INR 5/kWh, 2hr event):**

| Role | Inflows | Outflows | Net Position |
|------|---------|----------|-------------|
| **grid_operator** | - | 800 (savings payout) | **-800** (pays, but saves more in avoided procurement) |
| **aggregator** | 800 (from grid) | 500 (incentive to participant) | **+300** (margin) |
| **participant** | 500 (incentive) | - | **+500** (earns) |
| **Total** | | | **0.00** |

#### Example: EV Charging Revenue Model

```yaml
revenueModel:
  flows:
    - flowId: charging_payment
      from: ev_driver
      to: cpo
      flowType: ENERGY_PAYMENT
      formula:
        policyRef:
          type: REGO
          package: "deg.contracts.ev_charging"
          entrypoint: "total_charge"

    - flowId: tax
      from: ev_driver
      to: tax_authority
      flowType: TAX
      formula:
        expr: "chargingPayment * gstRate"

    - flowId: cancellation_refund
      from: cpo
      to: ev_driver
      flowType: CANCELLATION_FEE
      formula:
        expr: "-(paidAmount - cancellationFee)"    # Negative = refund net of fee
      triggeredBy: cancellation
```

#### Example: V2G Composite Revenue Model

```yaml
revenueModel:
  flows:
    # Charging direction: EV owner pays
    - flowId: charging_payment
      from: ev_owner
      to: cpo_aggregator
      flowType: ENERGY_PAYMENT
      formula:
        expr: "chargedKwh * chargingRate"

    # V2G direction: EV owner receives
    - flowId: v2g_payment
      from: cpo_aggregator
      to: ev_owner
      flowType: INCENTIVE
      formula:
        expr: "dischargedKwh * v2gRate"

    # Grid pays for V2G services
    - flowId: grid_v2g_payment
      from: grid_operator
      to: cpo_aggregator
      flowType: ENERGY_PAYMENT
      formula:
        expr: "dischargedKwh * gridV2gRate"
```

**Net payment for EV owner:**
```
netPosition(ev_owner) = v2gPayment - chargingPayment
```
If `dischargedKwh * v2gRate > chargedKwh * chargingRate`, the EV owner **earns money** from the transaction.

---

## 4. Mapping to Beckn Slots

The DEGContract maps to Beckn v2 core entities through attribute packs:

| DEGContract Part | Beckn Slot | When Used |
|-----------------|------------|-----------|
| `contractType` + `energySpec` | `Item.itemAttributes` | Catalog (on_search) |
| `roles[seller]` + partial `terms` | `Offer.offerAttributes` | Catalog (on_search) |
| `revenueModel.flows` (estimated) | `Offer.price` + `PriceSpecification.components` | Catalog (on_search) |
| `roles[buyer].inputs` filled | `Order.buyer.buyerAttributes` | Init, Confirm |
| Full `terms` + both roles filled | `Order.orderAttributes` | Confirm, Status |
| `revenueModel` (committed) | `Order.orderAttributes.revenueModel` | Confirm |
| `fulfillmentSpec` + delivery state | `OrderItem.orderItemAttributes.fulfillmentAttributes` | Status, Update |
| `revenueModel.flows[].computedAmount` | `Invoice` line items / `Payment` breakdown | Post-fulfillment |
| `settlementSpec` | `Payment` + `Invoice` | Post-fulfillment |

### 4.1 Lifecycle Mapping

```
Beckn Action    │  Contract State         │  What Happens
────────────────┼─────────────────────────┼──────────────────────────────
search          │  -                      │  BAP queries by contractType, energySpec
on_search       │  TEMPLATE               │  BPP returns catalog with partially-filled contracts
select          │  TEMPLATE → NEGOTIATED  │  BAP selects contract, fills buyer role inputs
on_select       │  NEGOTIATED             │  BPP returns quote with evaluated terms
init            │  NEGOTIATED → COMMITTED │  BAP provides credentials, meter IDs
on_init         │  COMMITTED              │  BPP verifies, returns final terms + payment link
confirm         │  COMMITTED → ACTIVE     │  Both parties sign off
on_confirm      │  ACTIVE                 │  Contract is live; fulfillment begins
status          │  ACTIVE                 │  Check fulfillment progress, term compliance
on_status       │  ACTIVE                 │  Return meter readings, signal state, compliance
update          │  ACTIVE                 │  Modify parameters (e.g., increase quantity)
on_update       │  ACTIVE                 │  Confirm modification
on_status(final)│  ACTIVE → SETTLED       │  All terms satisfied, settlement complete
cancel          │  * → CANCELLED          │  Cancellation terms apply
```

---

## 5. Inspirations and Parallels

### 5.1 From Arazzo (OpenAPI Workflows)

Arazzo defines multi-step API workflows with:
- **Workflows** with named steps, each referencing an API operation
- **Inputs/Outputs** declared per workflow and per step
- **Dependencies** between steps via `dependsOn`
- **Success/Failure criteria** and actions

**Parallel to DEG Contract:**
- Each Beckn action pair (search/on_search, select/on_select, etc.) is a "workflow step"
- Contract `terms` are like Arazzo's `successCriteria` — conditions that must be met for the step to succeed
- `RoleInput.providedAt` maps to Arazzo's concept of step-level inputs that flow from previous steps
- An Arazzo-style workflow description could formally specify the full DEG transaction flow

### 5.2 From OPA/Rego (Policy as Code)

OPA's key architectural insight: **decouple policy from the system being governed.**

```
        ┌──────────┐
Input → │   OPA    │ → Decision
        │ (Rego    │
Data  → │  Rules)  │
        └──────────┘
```

**Parallel to DEG Contract terms:**

```rego
# Example: Rego policy for a P2P energy delivery term
package deg.contracts.p2p_trade

import rego.v1

# The delivery obligation is satisfied when:
delivery_compliant if {
    input.deliveredQuantity >= data.contract.terms.minQuantity
    input.deliveredQuantity <= data.contract.terms.maxQuantity
    time.parse_rfc3339_ns(input.deliveryTime) >= time.parse_rfc3339_ns(data.contract.deliveryWindow.start)
    time.parse_rfc3339_ns(input.deliveryTime) <= time.parse_rfc3339_ns(data.contract.deliveryWindow.end)
}

# Deviation penalty calculation
deviation_penalty_inr := penalty if {
    not delivery_compliant
    shortfall := data.contract.terms.minQuantity - input.deliveredQuantity
    shortfall > 0
    penalty := shortfall * data.contract.terms.deviationPenaltyPerKwh
}

# Demand flexibility: trigger condition
demand_response_triggered if {
    input.gridFrequency < 49.5
}
demand_response_triggered if {
    input.priceSignal > data.contract.terms.priceThreshold
}
```

**In the DEGContract schema, this translates to:**

```yaml
terms:
  - termId: delivery_obligation
    termType: DELIVERY
    condition:
      expr: "currentTime WITHIN deliveryWindow"
    obligation:
      rule:
        operator: AND
        operands:
          - { field: "deliveredQuantity", operator: GTE, value: 10.0 }
          - { field: "deliveredQuantity", operator: LTE, value: 50.0 }
    consequence:
      expr: "penalty = shortfall * deviationPenaltyPerKwh"
    appliesTo: ["seller"]
```

For complex scenarios, the `policyRef` field allows pointing to actual Rego files:

```yaml
terms:
  - termId: demand_response_trigger
    termType: SIGNAL_RESPONSE
    condition:
      policyRef:
        type: REGO
        uri: "https://policies.deg-network.io/demand_flexibility/v1.rego"
        package: "deg.contracts.demand_flex"
        entrypoint: "demand_response_triggered"
    obligation:
      expr: "curtailLoad BY curtailmentTarget WITHIN responseWindow"
    appliesTo: ["consumer"]
```

### 5.3 From Ricardian Contracts

A Ricardian contract is both human-readable AND machine-parseable. The DEGContract achieves this:
- `terms[].description` (not shown above, but easy to add) provides human-readable text
- `terms[].condition/obligation` provides machine-parseable logic
- The `@context` JSON-LD mechanism from Beckn v2 provides semantic grounding

---

## 6. Design Principles

1. **Partially-filled templates**: The same contract structure works as a template (Offer) and as a committed agreement (Order). Empty `party` fields and null `value` fields in RoleInputs mark open slots.

2. **Progressive disclosure**: Simple contracts (fixed-price EV charging) need only `expr` strings. Complex contracts (multi-party demand flexibility with grid signals) can reference external Rego policies.

3. **Composability**: A COMPOSITE contract can combine terms from EV_CHARGING and DEMAND_FLEXIBILITY — e.g., "charge my EV but only during off-peak hours, and participate in V2G during grid stress."

4. **Evolvability**: New `contractType`, `roleType`, `termType`, `signalType` enums can be added without changing the schema structure. New policy expression types can be added to `PolicyExpression`.

5. **Beckn-native**: Every part maps to an existing Beckn v2 slot. No new API actions needed — only new attribute schemas.

6. **Net-zero revenue flows**: Every contract declares explicit monetary flows between roles. The invariant `sum(all flows) == 0` is enforced. Any agent can compute its role's net position in O(flows) time — no need to understand the whole contract, just filter by your roleId.
