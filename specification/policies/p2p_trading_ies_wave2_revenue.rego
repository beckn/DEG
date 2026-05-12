# DEG Contract Policy — P2P Trading Revenue Flows (wave2, timeseries)
#
# Computes the net revenue flow between the four roles in an inter-discom
# P2P energy trade and emits signed revenueFlows that sum to zero.
#
#   buyer        (energy consumer, BAP-side prosumer) → pays     → negative
#   seller       (energy producer, BPP-side prosumer) → receives → positive
#   buyerDiscom  (regulated LP for buyer's discom)    → receives → positive (wheeling)
#   sellerDiscom (regulated LP for seller's discom)   → receives → positive (wheeling + penalty)
#
# Multi-window: a single contract spans multiple delivery slots, each
# represented as an interval in two BecknTimeSeries:
#
#   commitments[0].offer.offerAttributes.inputs[seller].inputs.offerTimeseries
#       — PRICE_PER_KWH (currency: INR) and AVAILABLE_QTY (units: KWH)
#         one interval per slot; interval id is the slot key
#
#   contract.performance[0].performanceAttributes.performanceTimeseries
#       — BUYER_ALLOCATION, SELLER_INJECTION, SETTLED_QTY (all KWH)
#         interval ids match the offerTimeseries ids
#
# Per-slot trade value = SETTLED_QTY × PRICE_PER_KWH (matched by interval id).
# Total trade value = sum across all performance intervals.
#
# Wheeling and penalty placeholders are 0 today.
#
# Exported rules:
#   revenue_flows          — [{role, value, currency, description}]
#   trade_value            — total INR value across all intervals
#   total_settled_kwh      — total kWh settled across all intervals
#   wheeling_charge_buyer  — 0 placeholder
#   wheeling_charge_seller — 0 placeholder
#   penalty_charge         — 0 placeholder
#   net_zero_ok            — bool: sum of revenue_flows == 0
#   violations             — set of error strings

package deg.contracts.p2p_trading

import rego.v1

# ---------------------------------------------------------------------------
# Input extraction
# ---------------------------------------------------------------------------

_contract := input.message.contract

_offer_attrs := _contract.commitments[0].offer.offerAttributes

_inputs := _offer_attrs.inputs

_seller_inputs := [i.inputs | some i in _inputs; i.role == "seller"][0]

_offer_ts := _seller_inputs.offerTimeseries

_currency := _seller_inputs.currency

_perf_ts := _contract.performance[0].performanceAttributes.performanceTimeseries

# ---------------------------------------------------------------------------
# Timeseries helpers
# ---------------------------------------------------------------------------

# Scalar value of a typed payload within an interval.
_payload_val(interval, ptype) := v if {
	some p in interval.payloads
	p.type == ptype
	v := p.values[0]
}

# Seller offer interval id → price per kWh.
_price_by_id := {i.id: _payload_val(i, "PRICE_PER_KWH") | some i in _offer_ts.intervals}

# Set of offer interval ids (used for subset validation in violations).
_offer_interval_ids := {i.id | some i in _offer_ts.intervals}

# ---------------------------------------------------------------------------
# Per-interval value
# ---------------------------------------------------------------------------

_interval_value(pi) := v if {
	settled := _payload_val(pi, "SETTLED_QTY")
	price := _price_by_id[pi.id]
	v := settled * price
}

# ---------------------------------------------------------------------------
# Aggregate trade value across intervals
# ---------------------------------------------------------------------------

trade_value := sum([_interval_value(pi) | some pi in _perf_ts.intervals])

total_settled_kwh := sum([_payload_val(pi, "SETTLED_QTY") | some pi in _perf_ts.intervals])

_window_breakdown := concat("; ", [s |
	some pi in _perf_ts.intervals
	settled := _payload_val(pi, "SETTLED_QTY")
	price := _price_by_id[pi.id]
	value := settled * price
	s := sprintf("%v kWh @ %v %s = %v %s [interval %v]", [
		settled, price, _currency, value, _currency, pi.id,
	])
])

# ---------------------------------------------------------------------------
# Charge placeholders
# ---------------------------------------------------------------------------

default wheeling_charge_buyer := 0

default wheeling_charge_seller := 0

default penalty_charge := 0

# ---------------------------------------------------------------------------
# Revenue flows by role
# ---------------------------------------------------------------------------

_buyer_payable := trade_value + wheeling_charge_buyer

_seller_receivable := (trade_value - wheeling_charge_seller) - penalty_charge

_seller_discom_value := wheeling_charge_seller + penalty_charge

_buyer_flow := {
	"role": "buyer",
	"value": _buyer_payable * -1,
	"currency": _currency,
	"description": sprintf(
		"Pays %v %s across %v interval(s): [%s]; buyer-side wheeling %v",
		[_buyer_payable, _currency, count(_perf_ts.intervals), _window_breakdown, wheeling_charge_buyer],
	),
}

_seller_flow := {
	"role": "seller",
	"value": _seller_receivable,
	"currency": _currency,
	"description": sprintf(
		"Receives %v %s across %v interval(s): [%s]; seller-side wheeling %v, penalty %v",
		[_seller_receivable, _currency, count(_perf_ts.intervals), _window_breakdown, wheeling_charge_seller, penalty_charge],
	),
}

_buyer_discom_flow := {
	"role": "buyerDiscom",
	"value": wheeling_charge_buyer,
	"currency": _currency,
	"description": "Buyer-side wheeling charge across all intervals (placeholder — currently 0)",
}

_seller_discom_flow := {
	"role": "sellerDiscom",
	"value": _seller_discom_value,
	"currency": _currency,
	"description": "Seller-side wheeling charge + any penalty across all intervals (placeholders — currently 0)",
}

revenue_flows := [_buyer_flow, _seller_flow, _buyer_discom_flow, _seller_discom_flow]

_revenue_sum := sum([f.value | some f in revenue_flows])

net_zero_ok if _revenue_sum == 0

# ---------------------------------------------------------------------------
# Roles — extracted from contractAttributes
# ---------------------------------------------------------------------------

_contract_attrs := _contract.contractAttributes

_roles := {r.role | some r in _contract_attrs.roles}

# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

_required_roles := {"buyer", "seller", "buyerDiscom", "sellerDiscom"}

violations contains msg if {
	some role in _required_roles
	not role in _roles
	msg := sprintf("missing required role %q in contractAttributes.roles", [role])
}

violations contains msg if {
	count(_contract.performance) == 0
	msg := "no performance entries — cannot compute revenue flows"
}

violations contains msg if {
	count(_contract.performance) > 0
	not _contract.performance[0].performanceAttributes.performanceTimeseries
	msg := "performance[0].performanceAttributes.performanceTimeseries is missing"
}

violations contains msg if {
	some pi in _perf_ts.intervals
	not _payload_val(pi, "SETTLED_QTY")
	msg := sprintf("performance interval %v is missing SETTLED_QTY payload", [pi.id])
}

violations contains msg if {
	some pi in _perf_ts.intervals
	not pi.id in _offer_interval_ids
	msg := sprintf(
		"performance interval %v has no matching seller offer interval (available ids: %v)",
		[pi.id, _offer_interval_ids],
	)
}

violations contains msg if {
	not net_zero_ok
	msg := sprintf("net-zero failed: revenue sum = %g (expected 0)", [_revenue_sum])
}
