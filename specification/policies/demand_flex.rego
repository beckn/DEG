# DEG Contract Policy — Demand Flex Settlement
#
# Computes per-meter incentive payouts from M&V baselines/actuals,
# aggregates a portfolio total, and verifies net-zero revenue flows
# between utility (BPP) and aggregator (BAP).
#
# Input: full beckn on_status payload with:
#   - commitments[0].offer.offerAttributes  → incentive terms
#   - commitments[0].resources[0].resourceAttributes.eventWindow → hours
#   - performance[0].performanceAttributes  → baselines + actuals
#
# Exported rules:
#   settlement_components  — per-meter [{lineId, lineSummary, value, currency}]
#   total_settlement       — sum of all meter incentives
#   utility_outflow        — what the utility pays out
#   aggregator_inflow      — what the aggregator receives
#   net_zero_ok            — bool: outflow == inflow
#   event_hours            — derived from eventWindow
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

_incentive_per_kwh := _offer_attrs.incentivePerKwh

_currency := _offer_attrs.currency

_perf_attrs := input.message.contract.performance[0].performanceAttributes

_meters := _perf_attrs.meters

_event_window := _commitment.resources[0].resourceAttributes.eventWindow

# ---------------------------------------------------------------------------
# Event hours (from eventWindow)
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
# Exported: settlement components (consideration-ready line items)
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

# ---------------------------------------------------------------------------
# Exported: totals & net-zero
# ---------------------------------------------------------------------------

total_settlement := sum([s.incentive | some i; s := _meter_settlement[i]])

# Two-party model: utility pays out, aggregator receives.
# When network fees or multi-party splits are added, these diverge.
utility_outflow := total_settlement

aggregator_inflow := total_settlement

net_zero_ok if utility_outflow == aggregator_inflow

# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

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
	msg := sprintf("net-zero mismatch: utility outflow (%g) ≠ aggregator inflow (%g)",
		[utility_outflow, aggregator_inflow])
}
