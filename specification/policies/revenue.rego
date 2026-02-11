# DEG Contract Policy — Multi-Party Revenue Model (Net-Zero Flows)
#
# Generic revenue computation package. Evaluates the revenueModel declared
# in any DEGContract, computes each flow's amount, validates the net-zero
# invariant, and produces per-role revenue summaries that agents can query.
#
# input: { deliveredKwh, pricePerKwh, wheelingRate, ... }
# data.contract.revenueModel: { flows: [...] }
# data.contract.roles: [...]

package deg.revenue

import rego.v1

# --- Compute individual flow amounts ---

# P2P energy payment: buyer -> seller
flow_amount["energy_payment"] := amount if {
    some flow in data.contract.revenueModel.flows
    flow.flowId == "energy_payment"
    amount := input.deliveredKwh * input.pricePerKwh
}

# Wheeling charge: buyer -> utility
flow_amount["wheeling_charge"] := amount if {
    some flow in data.contract.revenueModel.flows
    flow.flowId == "wheeling_charge"
    amount := input.deliveredKwh * input.wheelingRatePerKwh
}

# Platform fee (buyer side): buyer -> platform
flow_amount["platform_fee_buyer"] := amount if {
    some flow in data.contract.revenueModel.flows
    flow.flowId == "platform_fee_buyer"
    amount := flow_amount["energy_payment"] * 0.01
}

# Platform fee (seller side): seller -> platform
flow_amount["platform_fee_seller"] := amount if {
    some flow in data.contract.revenueModel.flows
    flow.flowId == "platform_fee_seller"
    amount := flow_amount["energy_payment"] * 0.01
}

# Deviation penalty: seller -> buyer (only if delivery fell short)
flow_amount["deviation_penalty"] := amount if {
    some flow in data.contract.revenueModel.flows
    flow.flowId == "deviation_penalty"
    contracted := data.contract.energySpec.quantity.unitQuantity
    shortfall := contracted - input.deliveredKwh
    shortfall > 0
    amount := shortfall * input.deviationPenaltyPerKwh
}

flow_amount["deviation_penalty"] := 0 if {
    contracted := data.contract.energySpec.quantity.unitQuantity
    input.deliveredKwh >= contracted
}

# --- Per-role net position ---
# An agent queries: net_position["my_role_id"] to know if it earns or pays.
# Positive = earns money, Negative = pays money.

# Inflows for a role: sum of all flows where role is the recipient
inflows[role_id] := total if {
    some role in data.contract.roles
    role_id := role.roleId
    total := sum([amount |
        some flow in data.contract.revenueModel.flows
        flow.to == role_id
        amount := flow_amount[flow.flowId]
    ])
}

# Outflows for a role: sum of all flows where role is the payer
outflows[role_id] := total if {
    some role in data.contract.roles
    role_id := role.roleId
    total := sum([amount |
        some flow in data.contract.revenueModel.flows
        flow.from == role_id
        amount := flow_amount[flow.flowId]
    ])
}

# Net position per role
net_position[role_id] := position if {
    some role in data.contract.roles
    role_id := role.roleId
    position := inflows[role_id] - outflows[role_id]
}

# --- Net-zero invariant check ---

# Sum of all net positions must be zero
total_net := sum([pos | some role_id; pos := net_position[role_id]])

net_zero_valid if {
    abs(total_net) < 0.01  # Tolerance for floating point
}

# Helper
abs(x) := x if { x >= 0 }
abs(x) := y if { x < 0; y := 0 - x }

# --- Settlement summary ---
# Returns a structured object that agents can consume

# --- Settlement summary (individual fields) ---

settlement_flows := [flow_detail |
    some flow in data.contract.revenueModel.flows
    flow_detail := {
        "flowId": flow.flowId,
        "from": flow.from,
        "to": flow.to,
        "flowType": flow.flowType,
        "amount": flow_amount[flow.flowId],
        "currency": flow.currency,
    }
]
