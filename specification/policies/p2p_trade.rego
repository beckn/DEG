# DEG Contract Policy — P2P Energy Trading
#
# Evaluates delivery compliance, deviation penalties, sanctioned load checks,
# and settlement calculations for peer-to-peer energy trading contracts.
#
# input:  current transaction/event state (meter readings, timestamps)
# data.contract: the committed DEGContract terms
# data.meters: meter registry data (for sanctioned load checks)

package deg.contracts.p2p_trade

import rego.v1

# --- Delivery Compliance ---

# Check if delivery is within the contracted window
delivery_in_window if {
    now := time.now_ns()
    start := time.parse_rfc3339_ns(data.contract.fulfillmentSpec.deliveryWindow.startTime)
    end := time.parse_rfc3339_ns(data.contract.fulfillmentSpec.deliveryWindow.endTime)
    now >= start
    now <= end
}

# Check if delivered quantity meets the obligation (within 10% tolerance)
delivery_quantity_compliant if {
    contracted := data.contract.energySpec.quantity.unitQuantity
    delivered := input.deliveredQuantity
    delivered >= contracted * 0.9
    delivered <= contracted * 1.1
}

# Overall delivery compliance
delivery_compliant if {
    delivery_in_window
    delivery_quantity_compliant
}

# --- Deviation Penalty ---

# Calculate deviation penalty when delivery falls short
deviation_penalty := penalty if {
    not delivery_quantity_compliant
    contracted := data.contract.energySpec.quantity.unitQuantity
    delivered := input.deliveredQuantity
    shortfall := contracted - delivered
    shortfall > 0
    rate := data.contract.terms.deviationPenaltyPerKwh
    penalty := shortfall * rate
}

# No penalty if compliant
deviation_penalty := 0 if {
    delivery_quantity_compliant
}

# --- Sanctioned Load Check (for cascaded init to utility) ---

sanctioned_load_check if {
    meter_id := input.meterId
    requested := input.requestedQuantity
    sanctioned := data.meters[meter_id].sanctionedLoad
    requested <= sanctioned
}

# --- Settlement Calculation ---

settlement_amount := amount if {
    delivered := input.deliveredQuantity
    price := data.contract.terms.pricePerKwh
    wheeling := data.contract.terms.wheelingCharge
    amount := (delivered * price) + wheeling
}
