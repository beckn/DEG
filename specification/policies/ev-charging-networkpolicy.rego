# DEG Network Policy — EV Charging (uc2, settlement-first)
#
# Gate-only structural rules every message on the network must satisfy,
# evaluated by the `opapolicychecker` plugin on all four adapter modules.
# Every rule skips itself when its data is not on the wire, so the same
# policy spans catalog/publish through on_cancel without false positives.
# Settlement and party-agreed terms belong to ev-charging-contractpolicy.rego.
#
#   N1  Roles are exactly {driver, cpo}; cpo always bound, driver bound from select
#   N2  Offer `mode` agrees with `terms.reservation`; `reservedStart` present iff RESERVATION
#   N3  Reservation lead time: reservedStart − context.timestamp ≥ min_reservation_lead_min
#   N4  quote.promisedKW ≤ vehicle.maxChargeKW
#   N5  Ledger order: `at` strictly increasing, first row QUEUED/ASSIGNED, legal transitions
#   N6  Ledger fields: kWh iff energy state, stallId iff ASSIGNED, eventId iff LIMITED_BY_GRID
#   N7  Plausibility: average power of each energy row ≤ promisedKW × (1 + power_tolerance)
#   N8  Contract status matches the ledger: terminal ⇔ COMPLETE/CANCELLED
#
# Exported: violations.

package deg.policy.ev_charging_network

import rego.v1

# ==========================================================================
# NETWORK PARAMETERS
# ==========================================================================

min_reservation_lead_min := 60

power_tolerance := 0.05

# ==========================================================================
# END NETWORK PARAMETERS
# ==========================================================================

_action := input.context.action

_contract := input.message.contract

_ns_per_min := 60000000000

_energy_states := {"CHARGING", "LIMITED_BY_CPO", "LIMITED_BY_GRID"}

_terminal_states := {"DEPARTED", "CANCELLED", "NO_SHOW", "FAILED_BY_CPO"}

_next := {
	"QUEUED": {"ASSIGNED", "CANCELLED", "FAILED_BY_CPO"},
	"ASSIGNED": {"CHARGING", "QUEUED", "NO_SHOW", "CANCELLED", "FAILED_BY_CPO"},
	"CHARGING": {"LIMITED_BY_CPO", "LIMITED_BY_GRID", "IDLE", "DEPARTED", "FAILED_BY_CPO"},
	"LIMITED_BY_CPO": {"CHARGING", "LIMITED_BY_GRID", "IDLE", "DEPARTED", "FAILED_BY_CPO"},
	"LIMITED_BY_GRID": {"CHARGING", "LIMITED_BY_CPO", "IDLE", "DEPARTED", "FAILED_BY_CPO"},
	"IDLE": {"DEPARTED"},
}

# actions that carry a contract in which the driver has chosen an offer
_contract_actions := {
	"select", "on_select", "init", "on_init", "confirm", "on_confirm",
	"status", "on_status", "cancel", "on_cancel", "update", "on_update",
}

_lead_time_actions := {"select", "init", "confirm"}

# every ChargingOffer on the wire: catalog offers and committed offers
_offers contains offer if {
	some catalog in input.message.catalogs
	some offer in catalog.offers
	offer.offerAttributes["@type"] == "ChargingOffer"
}

_offers contains offer if {
	some c in _contract.commitments
	offer := c.offer
	offer.offerAttributes["@type"] == "ChargingOffer"
}

_ledger := perf.performanceAttributes.ledger if {
	some perf in _contract.performance
	perf.performanceAttributes["@type"] == "ChargingSession"
}

_t(i) := time.parse_rfc3339_ns(_ledger[i].at)

_promised_kw := c.commitmentAttributes.quote.promisedKW if {
	some c in _contract.commitments
}

# --------------------------------------------------------------------------
# N1 — roles
# --------------------------------------------------------------------------

_role_sets contains {"where": "catalog offer", "roles": offer.offerAttributes.contractAttributes.roles} if {
	some catalog in input.message.catalogs
	some offer in catalog.offers
}

_role_sets contains {"where": "contract", "roles": _contract.contractAttributes.roles} if {
	_contract.contractAttributes
}

violations contains msg if {
	some rs in _role_sets
	names := {r.role | some r in rs.roles}
	names != {"driver", "cpo"}
	msg := sprintf("N1: %v roles must be exactly {driver, cpo}, got %v", [rs.where, names])
}

violations contains msg if {
	some rs in _role_sets
	some r in rs.roles
	r.role == "cpo"
	not is_string(r.participantId)
	msg := sprintf("N1: %v role cpo must be bound to a participant", [rs.where])
}

violations contains msg if {
	_action in _contract_actions
	some r in _contract.contractAttributes.roles
	r.role == "driver"
	not is_string(r.participantId)
	msg := sprintf("N1: contract role driver must be bound from select (action %v)", [_action])
}

# --------------------------------------------------------------------------
# N2 — mode consistency
# --------------------------------------------------------------------------

violations contains msg if {
	some offer in _offers
	offer.offerAttributes.mode == "RESERVATION"
	not offer.offerAttributes.terms.reservation
	msg := sprintf("N2: offer %v is RESERVATION but has no terms.reservation", [offer.id])
}

violations contains msg if {
	some offer in _offers
	offer.offerAttributes.mode == "WALK_IN"
	offer.offerAttributes.terms.reservation
	msg := sprintf("N2: offer %v is WALK_IN but carries terms.reservation", [offer.id])
}

violations contains msg if {
	some c in _contract.commitments
	c.offer.offerAttributes.mode == "RESERVATION"
	c.commitmentAttributes
	not c.commitmentAttributes.reservedStart
	msg := sprintf("N2: commitment for RESERVATION offer %v has no reservedStart", [c.offer.id])
}

violations contains msg if {
	some c in _contract.commitments
	c.offer.offerAttributes.mode == "WALK_IN"
	c.commitmentAttributes.reservedStart
	msg := sprintf("N2: commitment for WALK_IN offer %v must not carry reservedStart", [c.offer.id])
}

# --------------------------------------------------------------------------
# N3 — reservation lead time
# --------------------------------------------------------------------------

violations contains msg if {
	_action in _lead_time_actions
	some c in _contract.commitments
	start := time.parse_rfc3339_ns(c.commitmentAttributes.reservedStart)
	lead_min := (start - time.parse_rfc3339_ns(input.context.timestamp)) / _ns_per_min
	lead_min < min_reservation_lead_min
	msg := sprintf("N3: reservation starts %v min after the request; the network requires at least %v min", [lead_min, min_reservation_lead_min])
}

# --------------------------------------------------------------------------
# N4 — promise within the vehicle's limit
# --------------------------------------------------------------------------

violations contains msg if {
	some c in _contract.commitments
	c.commitmentAttributes.quote.promisedKW > c.commitmentAttributes.vehicle.maxChargeKW
	msg := sprintf("N4: promisedKW %v exceeds vehicle maxChargeKW %v", [c.commitmentAttributes.quote.promisedKW, c.commitmentAttributes.vehicle.maxChargeKW])
}

# --------------------------------------------------------------------------
# N5 — ledger order and transitions
# --------------------------------------------------------------------------

violations contains msg if {
	first := _ledger[0].state
	not first in {"QUEUED", "ASSIGNED"}
	msg := sprintf("N5: ledger must start QUEUED or ASSIGNED, got %v", [_ledger[0].state])
}

violations contains msg if {
	some i, row in _ledger
	i > 0
	_t(i) <= _t(i - 1)
	msg := sprintf("N5: ledger row %v at %v is not after the previous row", [i, row.at])
}

violations contains msg if {
	some i, row in _ledger
	i > 0
	prev := _ledger[i - 1].state
	not row.state in object.get(_next, prev, set())
	msg := sprintf("N5: illegal transition %v -> %v at row %v", [prev, row.state, i])
}

# --------------------------------------------------------------------------
# N6 — conditional row fields
# --------------------------------------------------------------------------

_field_rules := [
	{"field": "kWh", "states": _energy_states},
	{"field": "stallId", "states": {"ASSIGNED"}},
	{"field": "eventId", "states": {"LIMITED_BY_GRID"}},
]

violations contains msg if {
	some i, row in _ledger
	some rule in _field_rules
	row.state in rule.states
	not rule.field in object.keys(row)
	msg := sprintf("N6: ledger row %v (%v) requires %v", [i, row.state, rule.field])
}

violations contains msg if {
	some i, row in _ledger
	some rule in _field_rules
	not row.state in rule.states
	rule.field in object.keys(row)
	msg := sprintf("N6: ledger row %v (%v) must not carry %v", [i, row.state, rule.field])
}

# --------------------------------------------------------------------------
# N7 — physical plausibility
# --------------------------------------------------------------------------

violations contains msg if {
	some i, row in _ledger
	row.state in _energy_states
	hours := (_t(i + 1) - _t(i)) / (_ns_per_min * 60)
	avg_kw := row.kWh / hours
	avg_kw > _promised_kw * (1 + power_tolerance)
	msg := sprintf("N7: ledger row %v averages %v kW, above promised %v kW", [i, avg_kw, _promised_kw])
}

# --------------------------------------------------------------------------
# N8 — contract status matches the ledger
# --------------------------------------------------------------------------

_last_state := _ledger[count(_ledger) - 1].state

_expected_status := "CANCELLED" if _last_state == "CANCELLED"

_expected_status := "COMPLETE" if _last_state in (_terminal_states - {"CANCELLED"})

_expected_status := "ACTIVE" if {
	state := _last_state
	not state in _terminal_states
}

violations contains msg if {
	_contract.status.code != _expected_status
	msg := sprintf("N8: contract status %v but the ledger implies %v", [_contract.status.code, _expected_status])
}
