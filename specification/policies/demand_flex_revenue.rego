# DEG Contract Policy — Demand Flex Revenue Flows
#
# Computes per-meter incentive payouts from M&V baselines/actuals and
# produces signed revenue flows per ROLE (buyer/seller), not per participant ID.
#
# buyer  (utility/DISCOM) → pays     → negative value
# seller (aggregator)     → receives → positive value
# Sum of all revenue_flows values MUST equal zero (net-zero).
#
# Input: full beckn contract payload with:
#   - contractAttributes.roles[].role            → buyer / seller
#   - commitments[0].offer.offerAttributes.terms → incentive terms (role-tagged)
#   - commitments[0].resources[0].resourceAttributes.eventWindow → hours
#   - performance[0].performanceAttributes       → baselines + actuals
#
# Exported rules:
#   revenue_flows          — [{role, value, currency, description}]
#   settlement_components  — per-meter [{lineId, lineSummary, value, currency}]
#   total_settlement       — sum of all meter incentives
#   event_hours            — derived from eventWindow
#   net_zero_ok            — bool: sum of revenue_flows == 0
#   violations             — set of error/warning strings

package deg.contracts.demand_flex

import rego.v1

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ns_per_hour := (1000 * 1000 * 1000) * 60 * 60

# ---------------------------------------------------------------------------
# Input extraction
# ---------------------------------------------------------------------------

_commitment := input.message.contract.commitments[0]

_offer_attrs := _commitment.offer.offerAttributes

_inputs := _offer_attrs.inputs

_buyer_inputs := [i.inputs | some i in _inputs; i.role == "buyer"][0]

_incentive_per_kwh := _buyer_inputs.incentivePerKwh

_currency := _buyer_inputs.currency

_perf_attrs := input.message.contract.performance[0].performanceAttributes

_meters := _perf_attrs.meters

_event_window := _commitment.resources[0].resourceAttributes.eventWindow

# ---------------------------------------------------------------------------
# Roles — extracted from contractAttributes (DEGContract)
# ---------------------------------------------------------------------------

_contract_attrs := input.message.contract.contractAttributes

_roles := {r.role | some r in _contract_attrs.roles}

# ---------------------------------------------------------------------------
# Event hours
# ---------------------------------------------------------------------------

_start_ns := time.parse_rfc3339_ns(_event_window.startDate)

_end_ns := time.parse_rfc3339_ns(_event_window.endDate)

event_hours := (_end_ns - _start_ns) / ns_per_hour

# ---------------------------------------------------------------------------
# Per-meter settlement
# ---------------------------------------------------------------------------

_clamp_zero(x) := x if x >= 0

_clamp_zero(x) := 0 if x < 0

_meter_settlement[i] := result if {
	meter := _meters[i]
	meter.actualKw != null
	reduction_kw := _clamp_zero(meter.baselineKw - meter.actualKw)
	reduction_kwh := reduction_kw * event_hours
	incentive := reduction_kwh * _incentive_per_kwh
	result := {
		"meterId": meter.meterId,
		"baselineKw": meter.baselineKw,
		"actualKw": meter.actualKw,
		"reductionKw": reduction_kw,
		"reductionKwh": reduction_kwh,
		"incentive": incentive,
	}
}

# ---------------------------------------------------------------------------
# Settlement components (per-meter line items)
# ---------------------------------------------------------------------------

settlement_components := [comp |
	some i
	s := _meter_settlement[i]
	comp := {
		"lineId": sprintf("incentive-%s", [s.meterId]),
		"lineSummary": sprintf("%s: (%g - %g) kW × %vh × %g %s/kWh",
			[s.meterId, s.baselineKw, s.actualKw, event_hours, _incentive_per_kwh, _currency]),
		"value": s.incentive,
		"currency": _currency,
	}
]

total_settlement := sum([s.incentive | some i; s := _meter_settlement[i]])

# ---------------------------------------------------------------------------
# Revenue flows by role (the core output)
#
#   buyer pays  → negative
#   seller receives → positive
#   sum = 0
# ---------------------------------------------------------------------------

_total_kwh := sum([s.reductionKwh | some i; s := _meter_settlement[i]])

_buyer_desc := sprintf("Incentive payable for %v kWh verified curtailment", [_total_kwh])

_seller_desc := sprintf("Incentive receivable for %v kWh verified curtailment", [_total_kwh])

_flow_defs := [
	["buyer", -1],
	["seller", 1],
]

revenue_flows := [flow |
	some def in _flow_defs
	role := def[0]
	sign := def[1]
	desc := sprintf("Incentive %s for %v kWh verified curtailment", [_flow_label[role], _total_kwh])
	flow := object.union(
		object.union(
			object.union({"role": role}, {"value": sign * total_settlement}),
			{"currency": _currency},
		),
		{"description": desc},
	)
]

_flow_label["buyer"] := "payable"

_flow_label["seller"] := "receivable"

_revenue_sum := sum([f.value | some f in revenue_flows])

net_zero_ok if _revenue_sum == 0

# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

violations contains msg if {
	not "buyer" in _roles
	msg := "no participant with role 'buyer' found"
}

violations contains msg if {
	not "seller" in _roles
	msg := "no participant with role 'seller' found"
}

violations contains msg if {
	some i
	meter := _meters[i]
	not meter.actualKw
	msg := sprintf("meter %s: missing actualKw — cannot compute settlement", [meter.meterId])
}

violations contains msg if {
	some i
	meter := _meters[i]
	meter.actualKw != null
	meter.actualKw > meter.baselineKw
	msg := sprintf("meter %s: actualKw (%g) > baselineKw (%g) — reduction clamped to zero",
		[meter.meterId, meter.actualKw, meter.baselineKw])
}

violations contains msg if {
	not net_zero_ok
	msg := sprintf("net-zero failed: revenue sum = %g (expected 0)", [_revenue_sum])
}
