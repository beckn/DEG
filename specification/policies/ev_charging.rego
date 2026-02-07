# DEG Contract Policy — EV Charging
#
# Evaluates connector compatibility, power feasibility, reservation checks,
# time-of-day pricing, and cancellation fees for EV charging contracts.
#
# input:  current charging session state (vehicle info, session status, energy delivered)
# data.contract: the committed DEGContract terms
# data.charger_state: real-time charger/EVSE state

package deg.contracts.ev_charging

import rego.v1

# --- Connector Compatibility ---

connector_compatible if {
    input.vehicleConnectorType == data.contract.inputs.connectorType
}

connector_compatible if {
    # CCS2 is backward compatible with Type2
    input.vehicleConnectorType == "Type2"
    data.contract.inputs.connectorType == "CCS2"
}

# --- Power Feasibility ---

power_feasible if {
    input.requestedPowerKW <= data.contract.inputs.maxPowerKW
    input.requestedPowerKW >= data.contract.inputs.minPowerKW
}

# --- Reservation Check ---

reservation_available if {
    data.contract.inputs.reservationSupported == true
    not data.charger_state.occupied
}

# --- Charging Price Calculation ---

# Time-of-day pricing
charging_price_per_kwh := price if {
    hour := time.clock(time.now_ns())[0]
    hour >= 22   # Off-peak: 10 PM - 6 AM
    price := data.contract.terms.offPeakRate
}

charging_price_per_kwh := price if {
    hour := time.clock(time.now_ns())[0]
    hour < 6     # Off-peak: 10 PM - 6 AM
    price := data.contract.terms.offPeakRate
}

charging_price_per_kwh := price if {
    hour := time.clock(time.now_ns())[0]
    hour >= 6
    hour < 10    # Normal: 6 AM - 10 AM
    price := data.contract.terms.normalRate
}

charging_price_per_kwh := price if {
    hour := time.clock(time.now_ns())[0]
    hour >= 10
    hour < 18    # Peak: 10 AM - 6 PM
    price := data.contract.terms.peakRate
}

charging_price_per_kwh := price if {
    hour := time.clock(time.now_ns())[0]
    hour >= 18
    hour < 22    # Normal: 6 PM - 10 PM
    price := data.contract.terms.normalRate
}

# Total charging cost
total_charge := cost if {
    cost := input.deliveredKwh * charging_price_per_kwh
}

# --- Cancellation Fee ---

cancellation_fee := fee if {
    input.fulfillmentState == "charging-started"
    fee := input.estimatedTotal * 0.30
}

cancellation_fee := 0 if {
    input.fulfillmentState == "order-initiated"
}
