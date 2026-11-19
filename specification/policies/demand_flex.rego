# DEG Contract Policy — Demand Flexibility
#
# Evaluates trigger conditions, event limits, curtailment measurement,
# and incentive calculations for demand flexibility contracts.
#
# input:  current grid/event state (frequency, price, load measurements)
# data.contract: the committed DEGContract terms
# data.events_this_month: array of events dispatched this billing month

package deg.contracts.demand_flex

import rego.v1

# --- Trigger Conditions ---

# Grid frequency drops below safe threshold
demand_response_triggered if {
    input.gridFrequency < 49.5
}

# Spot price exceeds contract threshold
demand_response_triggered if {
    input.spotPrice > data.contract.inputs.priceThreshold
}

# Explicit curtailment signal from grid operator
demand_response_triggered if {
    input.curtailmentSignal == "ACTIVE"
}

# --- Event Limit ---

# Check if monthly event limit is reached
events_exhausted if {
    count(data.events_this_month) >= data.contract.inputs.maxEventsPerMonth
}

# Event can be dispatched
event_allowed if {
    demand_response_triggered
    not events_exhausted
}

# --- Curtailment Measurement ---

# Calculate actual curtailment
actual_curtailment := reduction if {
    reduction := input.baselineLoad - input.actualLoad
    reduction > 0
}

actual_curtailment := 0 if {
    input.actualLoad >= input.baselineLoad
}

# Was curtailment sufficient? (80% of committed capacity)
curtailment_compliant if {
    actual_curtailment >= data.contract.inputs.curtailmentCapacity * 0.8
}

# --- Incentive Calculation ---

incentive_amount := amount if {
    curtailment_compliant
    hours := (input.eventEndNs - input.eventStartNs) / (3600 * 1000000000)
    amount := actual_curtailment * data.contract.inputs.incentiveRate * hours
}

incentive_amount := 0 if {
    not curtailment_compliant
}
