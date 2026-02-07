# DEG Contract Policy — Vehicle-to-Grid (V2G)
#
# Composite policy combining EV charging with demand flexibility.
# Evaluates V2G eligibility, discharge decisions, and net payment direction.
#
# input:  current vehicle/charger state (battery level, V2G capability, grid stress)
# data.contract: the committed DEGContract terms
# data.charger_state: real-time charger/EVSE state

package deg.contracts.v2g

import rego.v1

# --- V2G Eligibility ---

v2g_eligible if {
    input.vehicleBatteryPct > data.contract.inputs.minChargeLevelPct
    input.v2gCapable == true
    data.charger_state.v2gSupported == true
}

# --- Discharge Decision ---

should_discharge if {
    v2g_eligible
    input.gridStress == true
}

# Max discharge without going below min charge
max_discharge_kwh := kwh if {
    current_kwh := input.vehicleBatteryKwh * (input.vehicleBatteryPct / 100)
    min_kwh := input.vehicleBatteryKwh * (data.contract.inputs.minChargeLevelPct / 100)
    kwh := current_kwh - min_kwh
    kwh > 0
}

max_discharge_kwh := 0 if {
    current_kwh := input.vehicleBatteryKwh * (input.vehicleBatteryPct / 100)
    min_kwh := input.vehicleBatteryKwh * (data.contract.inputs.minChargeLevelPct / 100)
    current_kwh <= min_kwh
}

# --- Net Payment Direction ---

# Positive = EV owner pays, Negative = EV owner receives
net_payment := amount if {
    charged := input.totalChargedKwh * data.contract.terms.chargingRate
    discharged := input.totalDischargedKwh * data.contract.terms.v2gRate
    amount := charged - discharged
}
