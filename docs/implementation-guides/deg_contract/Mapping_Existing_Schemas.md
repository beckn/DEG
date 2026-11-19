# Mapping DEGContract to Existing Schemas

This document shows how the generalized DEGContract model maps to the existing `EvChargingService`, `EnergyTrade`, and `EnergyEnrollment` schemas from `protocol-specifications-v2/schema/`.

---

## 1. EV Charging as a DEGContract

### Current Schema Structure (EvChargingService v1)

```
Catalog
  └─ providers[]
       ├─ descriptor (name, images)
       ├─ locations[] (GPS coordinates)
       ├─ categories[] (green-tariff)
       ├─ fulfillments[] (type: CHARGING, stops, tags with connector specs)
       └─ items[]
            ├─ descriptor (code: "energy")
            ├─ price (value, currency: "INR/kWH")
            ├─ quantity.available (kWh)
            └─ fulfillment_ids, category_ids, location_ids
```

### As a DEGContract

```yaml
contractType: EV_CHARGING
version: "1.0.0"

roles:
  - roleId: cpo          # Charge Point Operator
    roleType: CPO
    party:                # Filled in catalog (they publish the template)
      partyId: "chargezone.in"
      partyType: PROVIDER
      platformId: "chargezone-energy-bpp.com"
      attributes:
        "@type": "ChargingService"    # from EvChargingService/v1
        connectorType: "CCS2"
        maxPowerKW: 60
        chargingStation:
          id: "IN-ECO-MDY-STATION-01"
          serviceLocation: { geo: { type: Point, coordinates: [77.6104, 12.9153] } }
    inputs:
      - inputId: charger_type
        inputType: PARAMETER
        value: "AC"                   # Pre-filled by CPO
        providedAt: TEMPLATE
      - inputId: connector_type
        inputType: PARAMETER
        value: "CCS2"
        providedAt: TEMPLATE
      - inputId: power_rating_kw
        inputType: PARAMETER
        value: 60
        providedAt: TEMPLATE

  - roleId: ev_driver
    roleType: CONSUMER
    party: null                       # Empty = open slot in catalog
    inputs:
      - inputId: requested_kwh
        inputType: PARAMETER
        required: true
        schema: { type: number, minimum: 1 }
        providedAt: NEGOTIATION       # Consumer fills during select
      - inputId: vehicle_details
        inputType: PARAMETER
        required: false
        providedAt: COMMITMENT        # Optional, during init
      - inputId: billing_info
        inputType: PARAMETER
        required: true
        providedAt: COMMITMENT

energySpec:
  energyType: ELECTRICAL
  sourceType: ANY
  quantity:
    unitText: "kWh"
    maxQuantity: 100                  # Available capacity

fulfillmentSpec:
  deliveryMode: EV_CHARGING
  location:
    geo: { type: Point, coordinates: [77.6104, 12.9153] }
  signals:
    - signalType: START_STOP
      protocol: OCPP

terms:
  - termId: pricing
    termType: PAYMENT
    condition:
      expr: "true"                    # Always applies
    obligation:
      expr: "payment = requestedKwh * pricePerKwh"
    appliesTo: ["ev_driver"]

  - termId: delivery
    termType: DELIVERY
    condition:
      expr: "paymentStatus == PAID"
    obligation:
      expr: "deliverEnergy(requestedKwh) AT selectedFulfillment"
    appliesTo: ["cpo"]

  - termId: cancellation
    termType: CANCELLATION
    condition:
      expr: "fulfillmentState IN [charging-start, charging-in-progress]"
    consequence:
      expr: "cancellationFee = 30%"
    appliesTo: ["ev_driver"]

settlementSpec:
  paymentType: PRE-ORDER
  currency: "INR"
```

### Field Mapping: Existing → DEGContract

| Existing EvCharging Field | DEGContract Location |
|--------------------------|---------------------|
| `provider.descriptor` | `roles[cpo].party.attributes.descriptor` |
| `provider.locations[]` | `fulfillmentSpec.location` |
| `items[].price` | `terms[pricing].obligation` |
| `items[].quantity.available` | `energySpec.quantity` |
| `fulfillments[].type: CHARGING` | `fulfillmentSpec.deliveryMode: EV_CHARGING` |
| `fulfillments[].tags` (connector specs) | `roles[cpo].inputs[]` |
| `fulfillments[].stops` | `fulfillmentSpec.deliveryWindow` |
| `order.billing` | `roles[ev_driver].inputs[billing_info]` |
| `cancellation_terms[]` | `terms[cancellation]` |
| `payments[].type: PRE-ORDER` | `settlementSpec.paymentType` |

---

## 2. P2P Energy Trade as a DEGContract

### Current Schema Structure (EnergyTrade v0.3)

```
Catalog
  └─ items[]
       ├─ itemAttributes: EnergyResource (sourceType, meterId, capacity)
       ├─ provider.providerAttributes: EnergyCustomer (meterId, utilityId)
       └─ offers[]
            ├─ price (PriceSpecification with applicableQuantity)
            └─ offerAttributes: EnergyTradeOffer (pricingModel, deliveryWindow)

Order
  ├─ orderAttributes: EnergyTradeOrder (bap_id, bpp_id, total_quantity)
  ├─ buyer.buyerAttributes: EnergyCustomer (meterId, utilityId)
  └─ orderItems[]
       └─ orderItemAttributes: EnergyOrderItem
            ├─ providerAttributes: EnergyCustomer (destination meter)
            └─ fulfillmentAttributes: EnergyTradeDelivery (meterReadings, deliveredQuantity)
```

### As a DEGContract

```yaml
contractType: P2P_ENERGY_TRADE
version: "0.3.0"

roles:
  - roleId: seller
    roleType: PROSUMER
    party:
      partyId: "solar-farm-001"
      partyType: PROVIDER
      platformId: "bpp.solarprovider.io"
      attributes:
        "@type": "EnergyCustomer"
        meterId: "der://meter/100200300"
        utilityId: "BESCOM-KA"
        sanctionedLoad: 25.0
    inputs:
      - inputId: source_meter
        inputType: METER_ID
        value: "der://meter/100200300"   # Pre-filled
        providedAt: TEMPLATE
      - inputId: energy_source
        inputType: PARAMETER
        value: "SOLAR"
        providedAt: TEMPLATE
      - inputId: available_kwh
        inputType: PARAMETER
        value: 30.5
        providedAt: TEMPLATE

  - roleId: buyer
    roleType: CONSUMER
    party: null                           # Open slot
    inputs:
      - inputId: destination_meter
        inputType: METER_ID
        required: true
        providedAt: NEGOTIATION
      - inputId: requested_kwh
        inputType: PARAMETER
        required: true
        schema: { type: number, minimum: 1, maximum: 30.5 }
        providedAt: NEGOTIATION
      - inputId: buyer_utility_id
        inputType: PARAMETER
        required: true
        providedAt: COMMITMENT

  - roleId: utility
    roleType: UTILITY
    party: null                           # Resolved via cascaded init
    inputs:
      - inputId: wheeling_charge
        inputType: PARAMETER
        providedAt: COMMITMENT            # Utility provides during cascaded init
        filledBy: "utility"

energySpec:
  energyType: ELECTRICAL
  sourceType: SOLAR
  quantity:
    unitText: "kWh"
    unitQuantity: 30.5
  qualityConstraints:
    greenCertRequired: true

fulfillmentSpec:
  deliveryMode: GRID_INJECTION
  deliveryWindow:
    "@type": "beckn:TimePeriod"
    schema:startTime: "2025-06-15T09:00:00Z"
    schema:endTime: "2025-06-15T17:00:00Z"
  meterIds: ["der://meter/100200300"]     # Seller's meter (buyer's added at negotiation)
  signals: []                              # No real-time signals for basic P2P

terms:
  - termId: delivery_obligation
    termType: DELIVERY
    condition:
      expr: "currentTime WITHIN deliveryWindow"
    obligation:
      rule:
        operator: AND
        operands:
          - { field: "deliveredQuantity", operator: GTE, value: "requestedKwh * 0.9" }
          - { field: "deliveredQuantity", operator: LTE, value: "requestedKwh * 1.1" }
    consequence:
      expr: "deviationPenalty = abs(deliveredQuantity - requestedKwh) * deviationPenaltyPerKwh"
    appliesTo: ["seller"]

  - termId: pricing
    termType: PAYMENT
    condition:
      expr: "true"
    obligation:
      expr: "payment = deliveredQuantity * pricePerKwh + wheelingCharge"
    appliesTo: ["buyer"]

  - termId: utility_registration
    termType: QUALITY
    condition:
      expr: "contractState == COMMITTED"
    obligation:
      policyRef:
        type: REGO
        package: "deg.contracts.p2p_trade"
        entrypoint: "sanctioned_load_check"
    appliesTo: ["utility"]

settlementSpec:
  paymentType: POST_DELIVERY
  currency: "INR"
  settlementCycle: "15_MIN"
```

### Field Mapping: Existing → DEGContract

| Existing EnergyTrade Field | DEGContract Location |
|---------------------------|---------------------|
| `EnergyResource.sourceType` | `energySpec.sourceType` / `roles[seller].inputs[energy_source]` |
| `EnergyResource.meterId` | `roles[seller].inputs[source_meter]` |
| `EnergyTradeOffer.pricingModel` | `terms[pricing]` |
| `EnergyTradeOffer.deliveryWindow` | `fulfillmentSpec.deliveryWindow` |
| `EnergyTradeOrder.bap_id` | `roles[buyer].party.platformId` |
| `EnergyTradeOrder.bpp_id` | `roles[seller].party.platformId` |
| `EnergyTradeOrder.total_quantity` | `energySpec.quantity` |
| `EnergyCustomer.meterId` (buyer) | `roles[buyer].inputs[destination_meter]` |
| `EnergyCustomer.utilityId` | `roles[buyer].inputs[buyer_utility_id]` |
| `EnergyTradeDelivery.deliveredQuantity` | Fulfillment state during `on_status` |
| `EnergyTradeDelivery.meterReadings` | Fulfillment state during `on_status` |

---

## 3. Demand Flexibility as a DEGContract

### Concept (No existing schema yet)

Demand flexibility involves a grid operator or aggregator signaling consumers to curtail or shift load in response to grid conditions (frequency, price, congestion).

### As a DEGContract

```yaml
contractType: DEMAND_FLEXIBILITY
version: "0.1.0"

roles:
  - roleId: aggregator
    roleType: AGGREGATOR
    party:
      partyId: "flex-agg-001"
      partyType: PROVIDER
      platformId: "bpp.flexaggregator.io"
    inputs:
      - inputId: program_name
        inputType: PARAMETER
        value: "Peak Shaving Q3 2025"
        providedAt: TEMPLATE
      - inputId: incentive_rate
        inputType: PARAMETER
        value: 5.0                        # INR per kWh curtailed
        providedAt: TEMPLATE
      - inputId: max_events_per_month
        inputType: PARAMETER
        value: 10
        providedAt: TEMPLATE

  - roleId: participant
    roleType: CONSUMER
    party: null
    inputs:
      - inputId: participant_meter
        inputType: METER_ID
        required: true
        providedAt: COMMITMENT
      - inputId: baseline_load_kw
        inputType: PARAMETER
        required: true
        schema: { type: number, minimum: 0 }
        providedAt: COMMITMENT
      - inputId: curtailment_capacity_kw
        inputType: PARAMETER
        required: true
        providedAt: COMMITMENT
      - inputId: enrollment_credential
        inputType: CREDENTIAL
        required: true
        providedAt: COMMITMENT

  - roleId: grid_operator
    roleType: GRID_OPERATOR
    party:
      partyId: "BESCOM"
      partyType: PROVIDER
      platformId: "bpp.bescom.gov.in"
    inputs:
      - inputId: grid_frequency_feed
        inputType: SIGNAL
        value: "mqtt://grid.bescom.gov.in/frequency"
        providedAt: TEMPLATE
      - inputId: curtailment_signal_topic
        inputType: SIGNAL
        value: "mqtt://grid.bescom.gov.in/curtailment"
        providedAt: TEMPLATE

energySpec:
  energyType: ELECTRICAL
  sourceType: ANY
  quantity:
    unitText: "kW"
    unitQuantity: 0                       # Demand response = negative supply
  qualityConstraints: {}

fulfillmentSpec:
  deliveryMode: LOAD_CURTAILMENT
  deliveryWindow:
    "@type": "beckn:TimePeriod"
    schema:startDate: "2025-07-01T00:00:00Z"
    schema:endDate: "2025-09-30T23:59:59Z"
  meterIds: []                            # Filled when participant enrolls
  signals:
    - signalType: GRID_FREQUENCY
      source: "mqtt://grid.bescom.gov.in/frequency"
      protocol: MQTT
    - signalType: CURTAILMENT_COMMAND
      source: "mqtt://grid.bescom.gov.in/curtailment"
      protocol: MQTT
    - signalType: PRICE_SIGNAL
      source: "https://api.iex.in/spot-price"
      protocol: HTTP_WEBHOOK

terms:
  - termId: trigger_condition
    termType: SIGNAL_RESPONSE
    condition:
      policyRef:
        type: REGO
        package: "deg.contracts.demand_flex"
        entrypoint: "demand_response_triggered"
    obligation:
      expr: "curtailLoad BY curtailmentCapacity WITHIN 15 minutes"
    appliesTo: ["participant"]

  - termId: measurement
    termType: DELIVERY
    condition:
      expr: "eventTriggered == true"
    obligation:
      rule:
        operator: GTE
        operands:
          - { field: "actualCurtailment" }
          - { field: "curtailmentCapacity * 0.8" }
    appliesTo: ["participant"]

  - termId: incentive_payment
    termType: PAYMENT
    condition:
      expr: "measurement.satisfied == true"
    obligation:
      expr: "incentive = actualCurtailment * incentiveRate * eventDurationHours"
    appliesTo: ["aggregator"]

  - termId: event_limit
    termType: QUALITY
    condition:
      expr: "eventsThisMonth >= maxEventsPerMonth"
    obligation:
      expr: "noMoreEvents UNTIL nextMonth"
    appliesTo: ["grid_operator"]

settlementSpec:
  paymentType: POST_DELIVERY
  currency: "INR"
  settlementCycle: "MONTHLY"
```

### Corresponding Rego Policy

```rego
package deg.contracts.demand_flex

import rego.v1

# Trigger: grid frequency drops below threshold
demand_response_triggered if {
    input.gridFrequency < 49.5
}

# Trigger: spot price exceeds threshold
demand_response_triggered if {
    input.spotPrice > data.contract.terms.priceThreshold
}

# Trigger: explicit curtailment signal received
demand_response_triggered if {
    input.curtailmentSignal == "ACTIVE"
}

# Measurement: was the curtailment sufficient?
curtailment_compliant if {
    reduction := input.baselineLoad - input.actualLoad
    reduction >= data.contract.inputs.curtailmentCapacity * 0.8
}

# Incentive calculation
incentive_amount := amount if {
    curtailment_compliant
    reduction := input.baselineLoad - input.actualLoad
    hours := (input.eventEnd - input.eventStart) / 3600
    amount := reduction * data.contract.inputs.incentiveRate * hours
}
```

---

## 4. Composite Contract Example

A V2G (Vehicle-to-Grid) scenario combines EV Charging + Demand Flexibility:

```yaml
contractType: COMPOSITE
version: "0.1.0"

roles:
  - roleId: ev_owner
    roleType: PROSUMER              # Both consumes (charging) and produces (V2G)
    inputs:
      - inputId: vehicle_battery_kwh
        inputType: PARAMETER
        required: true
        providedAt: NEGOTIATION
      - inputId: min_charge_level_pct
        inputType: PARAMETER
        value: 30                   # Never drain below 30%
        providedAt: NEGOTIATION

  - roleId: cpo_aggregator
    roleType: AGGREGATOR            # Both CPO and demand flexibility aggregator
    inputs:
      - inputId: v2g_rate_per_kwh
        inputType: PARAMETER
        value: 6.0
        providedAt: TEMPLATE

terms:
  # EV Charging terms
  - termId: charging
    termType: DELIVERY
    condition:
      expr: "gridStress == false"
    obligation:
      expr: "chargeVehicle AT requestedRate"
    appliesTo: ["cpo_aggregator"]

  # V2G discharge terms
  - termId: v2g_discharge
    termType: SIGNAL_RESPONSE
    condition:
      rule:
        operator: AND
        operands:
          - { field: "gridStress", operator: EQ, value: true }
          - { field: "vehicleBatteryPct", operator: GTE, value: "minChargeLevelPct" }
    obligation:
      expr: "dischargeToGrid AT maxAvailableRate"
    appliesTo: ["ev_owner"]

  # Payment flows both ways
  - termId: charging_payment
    termType: PAYMENT
    condition:
      expr: "energyFlowDirection == TO_VEHICLE"
    obligation:
      expr: "evOwner PAYS chargingRate * kwhDelivered"
    appliesTo: ["ev_owner"]

  - termId: v2g_payment
    termType: PAYMENT
    condition:
      expr: "energyFlowDirection == FROM_VEHICLE"
    obligation:
      expr: "cpoAggregator PAYS v2gRate * kwhDischarged"
    appliesTo: ["cpo_aggregator"]

revenueModel:
  flows:
    # Normal charging: EV owner pays CPO
    - flowId: charging_payment
      from: ev_owner
      to: cpo_aggregator
      flowType: ENERGY_PAYMENT
      formula:
        expr: "chargedKwh * chargingRate"
      triggeredBy: charging_payment

    # V2G discharge: CPO pays EV owner
    - flowId: v2g_payment
      from: cpo_aggregator
      to: ev_owner
      flowType: INCENTIVE
      formula:
        expr: "dischargedKwh * v2gRate"
      triggeredBy: v2g_payment

    # Grid operator pays CPO for V2G ancillary services
    - flowId: grid_ancillary_payment
      from: grid_operator
      to: cpo_aggregator
      flowType: GRID_SERVICE_FEE
      formula:
        expr: "dischargedKwh * gridAncillaryRate"

    # Platform fee
    - flowId: platform_fee
      from: cpo_aggregator
      to: platform
      flowType: PLATFORM_FEE
      formula:
        expr: "(chargingPayment + gridAncillaryPayment) * 0.015"
```

**Per-role revenue view (charged 20 kWh @ INR 8, discharged 5 kWh @ INR 12 V2G, grid pays INR 15/kWh):**

| Role | Inflows | Outflows | Net Position | Direction |
|------|---------|----------|-------------|-----------|
| **ev_owner** | 60 (V2G) | 160 (charging) | **-100** | PAYS |
| **cpo_aggregator** | 160 (charging) + 75 (grid) = 235 | 60 (V2G) + 3.53 (fee) = 63.53 | **+171.47** | RECEIVES |
| **grid_operator** | - | 75 (ancillary) | **-75** | PAYS |
| **platform** | 3.53 (fee) | - | **+3.53** | RECEIVES |
| **Total** | | | **0.00** | |

An agent for `ev_owner` instantly sees: "I pay INR 100 net, but get 5 kWh discharged credit worth INR 60. My effective charging cost is INR 100 for 20 kWh = INR 5/kWh instead of INR 8/kWh."

---

## 5. How Agents Query Their Revenue Incentive

Each agent acting on behalf of a role needs to answer one question: **"What's in it for me?"**

### 5.1 Query Pattern

```
GET /settlement/my-position?roleId={roleId}&contractId={contractId}
```

Returns (computed by Rego `deg.revenue.net_position`):

```json
{
  "roleId": "seller",
  "contractId": "contract-p2p-001",
  "position": {
    "inflows": [
      { "flowId": "energy_payment", "from": "buyer", "amount": 45.00, "type": "ENERGY_PAYMENT" }
    ],
    "outflows": [
      { "flowId": "platform_fee_seller", "to": "platform", "amount": 0.45, "type": "PLATFORM_FEE" }
    ],
    "netAmount": 44.55,
    "currency": "INR",
    "direction": "RECEIVES"
  },
  "incentiveSummary": "You earn INR 44.55 for delivering 10 kWh of solar energy."
}
```

### 5.2 Pre-Commitment Revenue Preview

Before a party accepts a role, they can preview their revenue position from the template:

```
POST /contract/preview-revenue
Body: { contractId, roleId, estimatedInputs: { requestedKwh: 10, ... } }
```

This evaluates the `revenueModel.flows` with estimated values, so the agent knows:
- "If I accept this contract and deliver 10 kWh, I'll earn approximately INR 44.55"
- "If I curtail 5 kW for 2 hours, I'll earn approximately INR 50"

### 5.3 Multi-Contract Portfolio View

An agent managing multiple contracts can aggregate across all of them:

```json
{
  "agentId": "solar-farm-001",
  "roleId": "seller",
  "portfolio": [
    { "contractId": "p2p-001", "net": 44.55, "status": "ACTIVE" },
    { "contractId": "p2p-002", "net": 89.10, "status": "ACTIVE" },
    { "contractId": "flex-001", "net": 150.00, "status": "SETTLED" }
  ],
  "totalNetPosition": 283.65,
  "currency": "INR"
}
```

---

## 6. Migration Strategy

The generalized DEGContract does NOT replace existing schemas. Instead:

1. **Existing schemas remain** as the concrete attribute packs (ChargingService, EnergyResource, EnergyCustomer, etc.)
2. **DEGContract** is a **new Offer/Order-level attribute pack** that wraps the existing ones with a contract-oriented view
3. **Incremental adoption**: Platforms can start using DEGContract for new use cases (demand flexibility) while keeping existing schemas for established flows

```
                    ┌──────────────────────────────────┐
                    │          DEGContract              │
                    │    (Order.orderAttributes)        │
                    │                                   │
                    │  roles[] ──→ Provider/Buyer       │
                    │  terms[] ──→ PolicyExpr/Rego      │
                    │  energySpec ──→ Item.attrs        │
                    │  fulfillmentSpec ──→ Fulfmt       │
                    │  revenueModel ──→ Net-zero flows  │
                    │     │                             │
                    │     ├─ flow[0]: buyer→seller      │
                    │     ├─ flow[1]: buyer→utility     │
                    │     └─ Σ(all flows) == 0          │
                    └──────────┬───────────────────────┘
                               │ references
                    ┌──────────┴──────────────────┐
                    │   Existing Attribute Packs   │
                    │                              │
                    │  ChargingService (Item)       │
                    │  EnergyResource (Item)        │
                    │  EnergyCustomer (Buyer/Prov)  │
                    │  EnergyTradeDelivery (Fulfmt) │
                    │  EnergyEnrollment (Fulfmt)    │
                    └──────────────────────────────┘
```
