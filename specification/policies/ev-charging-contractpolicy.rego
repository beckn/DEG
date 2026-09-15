# DEG Contract Policy — EV Charging (walk-in and reservation)
#
# One policy for both contract modes: a reservation is a walk-in plus a
# premium and a guarantee, so reservation terms add lines rather than a second
# policy. The policy holds formulas only; every number comes from the offer's
# EvChargingOffer v3.0 `terms`. Settlement is a pure function of those terms,
# the commitment quote (EvChargingCommitment v1.0) and the session ledger
# (EvChargingSession v3.0), so both counterparties compute the same invoice.
#
# Ledger rows hold a state from `at` until the next row's `at`. With
# P = quote.promisedKW and, per energy row k, duration Δt_k (min), energy e_k:
#
#   added_k     = 60 · max(0, P·Δt_k/60 − e_k) / P       minutes a LIMITED_* row added
#   occupancy   = (Σ Δt_energy − addedCpo − addedGrid) · occupancyPerMin
#   energy      = Σ e_k · energyPerKWh
#   idle        = max(0, Δt_IDLE − graceMin) · idlePerMin
#   reservation = fee, when kept (see _fee_kept)
#   cpoCredit   = min((lateMin + addedCpo) · cpoDelayCreditPerMin, liabilityCap)
#   gridCredit  = addedGrid · gridDelayCreditPerMin
#   lateMin     = max(0, firstAssigned − reservedStart − graceMin)   RESERVATION only
#
# Credits pay for time, not energy: a limit delivers energy later, it does not
# take it away. A fault or full suspension is the same formula at e_k = 0.
#
# Output: each non-zero line becomes a net-zero pair of RevenueFlow entries
# (payer −amount, payee +amount). revenue_flows is defined only once the
# ledger ends in a terminal state and at least one line is non-zero.
#
# Structural well-formedness (legal transitions, conditional row fields,
# lead time, plausibility) is owned by ev-charging-networkpolicy.rego. This
# policy checks only party-agreed terms, and every rule is valid at any stage
# of the ledger, so on_status can be enforced.
#
# Exported: revenue_flows, settlement_lines, total_driver_payable, violations.

package deg.contracts.ev_charging

import rego.v1

_energy_states := {"CHARGING", "LIMITED_BY_CPO", "LIMITED_BY_GRID"}

_terminal_states := {"DEPARTED", "CANCELLED", "NO_SHOW", "FAILED_BY_CPO"}

_ns_per_min := 60000000000

# --------------------------------------------------------------------------
# Input extraction
# --------------------------------------------------------------------------

_contract := input.message.contract

_commitment := _contract.commitments[0]

_offer := _commitment.offer.offerAttributes

_terms := _offer.terms

_currency := _terms.currency

_grace := _terms.graceMin

_request := _commitment.commitmentAttributes

_promised_kw := _request.quote.promisedKW

_ledger := perf.performanceAttributes.ledger if {
	some perf in _contract.performance
	perf.performanceAttributes["@type"] == "ChargingSession"
}

_n := count(_ledger)

_terminal := _ledger[_n - 1] if _ledger[_n - 1].state in _terminal_states

# --------------------------------------------------------------------------
# Ledger derivations
# --------------------------------------------------------------------------

_t(i) := time.parse_rfc3339_ns(_ledger[i].at)

# duration of row i in minutes; undefined for the last row
_dur(i) := (_t(i + 1) - _t(i)) / _ns_per_min

_added(i) := (60 * max([0, ((_promised_kw * _dur(i)) / 60) - _ledger[i].kWh])) / _promised_kw

_energy_kwh := sum([row.kWh | some row in _ledger; row.state in _energy_states])

_on_stall_min := sum([_dur(i) | some i, row in _ledger; row.state in _energy_states])

_added_cpo := sum([_added(i) | some i, row in _ledger; row.state == "LIMITED_BY_CPO"])

_added_grid := sum([_added(i) | some i, row in _ledger; row.state == "LIMITED_BY_GRID"])

_idle_min := sum([_dur(i) | some i, row in _ledger; row.state == "IDLE"])

_billable_idle_min := max([0, _idle_min - _grace])

_billable_occupancy_min := max([0, (_on_stall_min - _added_cpo) - _added_grid])

# demotion: an ASSIGNED row followed by QUEUED
_demotions := count([i | some i, row in _ledger; row.state == "ASSIGNED"; _ledger[i + 1].state == "QUEUED"])

_reserved_start_ns := time.parse_rfc3339_ns(_request.reservedStart)

_assigned_ns := [_t(i) | some i, row in _ledger; row.state == "ASSIGNED"]

# moment the CPO made a stall ready; if it never did and failed, the failure
_ready_ns := min(_assigned_ns) if count(_assigned_ns) > 0

_ready_ns := _t(_n - 1) if {
	count(_assigned_ns) == 0
	_terminal.state == "FAILED_BY_CPO"
}

default _late_min := 0

_late_min := max([0, ((_ready_ns - _reserved_start_ns) / _ns_per_min) - _grace]) if _offer.mode == "RESERVATION"

default _fee_kept := false

_fee_kept if {
	_terminal.state == "DEPARTED"
	_late_min == 0
}

_fee_kept if _terminal.state == "NO_SHOW"

_fee_kept if {
	_terminal.state == "CANCELLED"
	(_reserved_start_ns - _t(_n - 1)) / _ns_per_min < _terms.reservation.cancelBeforeMin
}

# --------------------------------------------------------------------------
# Settlement lines
# --------------------------------------------------------------------------

_r2(x) := round(x * 100) / 100

# Each line defaults to null when its inputs are absent (e.g. reservation
# lines on a walk-in offer); nulls and zero amounts are dropped below.
default _energy_line := null

default _occupancy_line := null

default _idle_line := null

default _reservation_line := null

default _cpo_credit_line := null

default _grid_credit_line := null

_energy_line := {"payer": "driver", "payee": "cpo", "amount": _r2(_energy_kwh * _terms.energyPerKWh), "description": sprintf("energy: %v kWh at %v %v/kWh", [_r2(_energy_kwh), _terms.energyPerKWh, _currency])}

_occupancy_line := {"payer": "driver", "payee": "cpo", "amount": _r2(_billable_occupancy_min * _terms.occupancyPerMin), "description": sprintf("occupancy: %v min at %v %v/min (%v min on stall, %v added by CPO limits, %v by grid limits)", [_r2(_billable_occupancy_min), _terms.occupancyPerMin, _currency, _r2(_on_stall_min), _r2(_added_cpo), _r2(_added_grid)])}

_idle_line := {"payer": "driver", "payee": "cpo", "amount": _r2(_billable_idle_min * _terms.idlePerMin), "description": sprintf("idle: %v min beyond %v min grace at %v %v/min", [_r2(_billable_idle_min), _grace, _terms.idlePerMin, _currency])}

_grid_credit_line := {"payer": "cpo", "payee": "driver", "amount": _r2(_added_grid * _terms.gridDelayCreditPerMin), "description": sprintf("grid delay credit: %v min added by grid events at %v %v/min", [_r2(_added_grid), _terms.gridDelayCreditPerMin, _currency])}

_reservation_line := {"payer": "driver", "payee": "cpo", "amount": _r2(_terms.reservation.fee), "description": sprintf("reservation fee kept (%v)", [_terminal.state])} if _fee_kept

_cpo_credit_uncapped := (_late_min + _added_cpo) * _terms.reservation.cpoDelayCreditPerMin

_cpo_credit_line := {"payer": "cpo", "payee": "driver", "amount": _r2(min([_cpo_credit_uncapped, _terms.reservation.liabilityCap])), "description": sprintf("CPO delay credit: %v min (%v late start beyond grace, %v added by CPO limits) at %v %v/min, cap %v", [_r2(_late_min + _added_cpo), _r2(_late_min), _r2(_added_cpo), _terms.reservation.cpoDelayCreditPerMin, _currency, _terms.reservation.liabilityCap])} if _offer.mode == "RESERVATION"

_lines_in_order := [_energy_line, _occupancy_line, _idle_line, _reservation_line, _cpo_credit_line, _grid_credit_line]

settlement_lines := [line | some line in _lines_in_order; line != null; line.amount > 0] if _terminal

total_driver_payable := _r2(sum([_signed_driver(line) | some line in lines])) if lines := settlement_lines

_signed_driver(line) := line.amount if line.payer == "driver"

_signed_driver(line) := 0 - line.amount if line.payee == "driver"

_pair(line) := [
	{"role": line.payer, "value": neg, "currency": _currency, "description": line.description},
	{"role": line.payee, "value": line.amount, "currency": _currency, "description": line.description},
] if {
	neg := 0 - line.amount
}

revenue_flows := [flow | some line in settlement_lines; some flow in _pair(line)] if count(settlement_lines) > 0

# --------------------------------------------------------------------------
# Violations — party-agreed terms only
# --------------------------------------------------------------------------

# C1 — a demotion only after the ASSIGNED row lasted at least graceMin
violations contains msg if {
	some i, row in _ledger
	row.state == "ASSIGNED"
	_ledger[i + 1].state == "QUEUED"
	_dur(i) < _grace
	msg := sprintf("C1: driver demoted at %v after %v min on ASSIGNED; grace is %v min", [_ledger[i + 1].at, _dur(i), _grace])
}

# C2 — NO_SHOW only after maxDemotions demotions and a full grace on the last assignment
violations contains msg if {
	_terminal.state == "NO_SHOW"
	_demotions < _terms.maxDemotions
	msg := sprintf("C2: NO_SHOW after %v demotion(s); the offer allows %v", [_demotions, _terms.maxDemotions])
}

violations contains msg if {
	_terminal.state == "NO_SHOW"
	_ledger[_n - 2].state == "ASSIGNED"
	_dur(_n - 2) < _grace
	msg := sprintf("C2: NO_SHOW declared %v min after assignment; grace is %v min", [_dur(_n - 2), _grace])
}

# C3 — revenue flows net to zero (backstop)
violations contains msg if {
	total := sum([flow.value | some flow in revenue_flows])
	abs(total) > 0.001
	msg := sprintf("C3: revenue flows sum to %v, expected 0", [total])
}
