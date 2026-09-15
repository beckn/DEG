package deg.contracts.ev_charging_test

import rego.v1

import data.deg.contracts.ev_charging

_walk_in_terms := {"currency": "INR", "energyPerKWh": 18, "occupancyPerMin": 2, "idlePerMin": 10, "graceMin": 5, "maxDemotions": 2, "gridDelayCreditPerMin": 1}

_reservation_terms := object.union(_walk_in_terms, {"reservation": {"fee": 100, "cancelBeforeMin": 60, "cpoDelayCreditPerMin": 5, "liabilityCap": 500}})

_msg(mode, ledger) := {"context": {"action": "on_status", "timestamp": "2026-10-02T19:05:00Z"}, "message": {"contract": {
	"status": {"code": "COMPLETE"},
	"commitments": [{
		"offer": {"id": "o", "offerAttributes": {"@type": "ChargingOffer", "mode": mode, "terms": _terms(mode)}},
		"commitmentAttributes": object.union({"vehicle": {"maxChargeKW": 60}, "quote": {"promisedKW": 60}}, _reserved(mode)),
	}],
	"performance": [{"performanceAttributes": {"@type": "ChargingSession", "ledger": ledger}}],
}}}

_terms("WALK_IN") := _walk_in_terms

_terms("RESERVATION") := _reservation_terms

_reserved("WALK_IN") := {}

_reserved("RESERVATION") := {"reservedStart": "2026-10-02T18:00:00Z"}

_row(at, state) := {"at": sprintf("2026-10-02T%v:00Z", [at]), "state": state}

_energy(at, state, kwh) := object.union(_row(at, state), {"kWh": kwh})

_worked_example := [
	_row("12:05", "QUEUED"),
	object.union(_row("18:12", "ASSIGNED"), {"stallId": "A1"}),
	_energy("18:15", "CHARGING", 10.0),
	object.union(_energy("18:25", "LIMITED_BY_GRID", 5.0), {"eventId": "DR-1"}),
	_energy("18:35", "LIMITED_BY_CPO", 0),
	_energy("18:39", "CHARGING", 16.0),
	_row("18:55", "IDLE"),
	_row("19:04", "DEPARTED"),
]

_amount(lines, prefix) := [l.amount | some l in lines; startswith(l.description, prefix)][0]

# ── Reservation worked example (DESIGN.md §8.1) ──

test_worked_example_total if {
	ev_charging.total_driver_payable == 600 with input as _msg("RESERVATION", _worked_example)
}

test_worked_example_lines if {
	lines := ev_charging.settlement_lines with input as _msg("RESERVATION", _worked_example)
	_amount(lines, "energy") == 558
	_amount(lines, "occupancy") == 62
	_amount(lines, "idle") == 40
	_amount(lines, "CPO delay credit") == 55
	_amount(lines, "grid delay credit") == 5
	count([l | some l in lines; startswith(l.description, "reservation fee")]) == 0
}

test_worked_example_flows_are_net_zero_pairs if {
	flows := ev_charging.revenue_flows with input as _msg("RESERVATION", _worked_example)
	count(flows) == 10
	sum([f.value | some f in flows]) == 0
	sum([f.value | some f in flows; f.role == "driver"]) == -600
	count(ev_charging.violations) == 0 with input as _msg("RESERVATION", _worked_example)
}

test_on_time_departure_keeps_fee if {
	ledger := [
		_row("12:05", "QUEUED"),
		object.union(_row("18:04", "ASSIGNED"), {"stallId": "A1"}),
		_energy("18:06", "CHARGING", 30.0),
		_row("18:36", "DEPARTED"),
	]
	lines := ev_charging.settlement_lines with input as _msg("RESERVATION", ledger)
	_amount(lines, "reservation fee") == 100
	count([l | some l in lines; startswith(l.description, "CPO delay credit")]) == 0
}

# ── Walk-in ──

test_walk_in_with_demotion if {
	ledger := [
		_row("10:01", "QUEUED"),
		object.union(_row("10:20", "ASSIGNED"), {"stallId": "A1"}),
		_row("10:27", "QUEUED"),
		object.union(_row("10:31", "ASSIGNED"), {"stallId": "A2"}),
		_energy("10:34", "CHARGING", 24.0),
		_row("11:04", "IDLE"),
		_row("11:12", "DEPARTED"),
	]
	m := _msg("WALK_IN", ledger)
	ev_charging.total_driver_payable == 522 with input as m
	count(ev_charging.settlement_lines) == 3 with input as m
	count(ev_charging.violations) == 0 with input as m
}

test_walk_in_limits_earn_grid_credit_but_no_cpo_credit if {
	ledger := [
		object.union(_row("10:00", "ASSIGNED"), {"stallId": "A1"}),
		_energy("10:02", "LIMITED_BY_CPO", 0),
		object.union(_energy("10:12", "LIMITED_BY_GRID", 0), {"eventId": "DR-1"}),
		_row("10:22", "DEPARTED"),
	]
	lines := ev_charging.settlement_lines with input as _msg("WALK_IN", ledger)
	count([l | some l in lines; startswith(l.description, "CPO delay credit")]) == 0
	count([l | some l in lines; startswith(l.description, "occupancy")]) == 0
	_amount(lines, "grid delay credit") == 10
}

# ── Settlement waits for a terminal row ──

test_no_flows_before_terminal if {
	not ev_charging.revenue_flows with input as _msg("RESERVATION", array.slice(_worked_example, 0, 4))
	not ev_charging.total_driver_payable with input as _msg("RESERVATION", array.slice(_worked_example, 0, 4))
}

# ── Reservation fee disposition ──

test_late_cancel_forfeits_fee if {
	ledger := [_row("12:05", "QUEUED"), _row("17:30", "CANCELLED")]
	ev_charging.total_driver_payable == 100 with input as _msg("RESERVATION", ledger)
}

test_early_cancel_refunds_fee if {
	ledger := [_row("12:05", "QUEUED"), _row("16:30", "CANCELLED")]
	not ev_charging.revenue_flows with input as _msg("RESERVATION", ledger)
}

test_cpo_failure_refunds_and_credits_lateness_to_failure if {
	ledger := [_row("12:05", "QUEUED"), _row("18:25", "FAILED_BY_CPO")]
	lines := ev_charging.settlement_lines with input as _msg("RESERVATION", ledger)
	count(lines) == 1
	_amount(lines, "CPO delay credit") == 100
}

test_cpo_credit_is_capped if {
	ledger := [
		_row("12:05", "QUEUED"),
		object.union(_row("18:00", "ASSIGNED"), {"stallId": "A1"}),
		_energy("18:02", "LIMITED_BY_CPO", 0),
		_row("20:02", "FAILED_BY_CPO"),
	]
	lines := ev_charging.settlement_lines with input as _msg("RESERVATION", ledger)
	_amount(lines, "CPO delay credit") == 500
}

# ── Violations ──

test_c1_early_demotion if {
	ledger := [
		_row("10:01", "QUEUED"),
		object.union(_row("10:20", "ASSIGNED"), {"stallId": "A1"}),
		_row("10:23", "QUEUED"),
	]
	some v in ev_charging.violations with input as _msg("WALK_IN", ledger)
	startswith(v, "C1:")
}

test_c2_no_show_before_demotions_exhausted if {
	ledger := [
		_row("12:05", "QUEUED"),
		object.union(_row("18:00", "ASSIGNED"), {"stallId": "A1"}),
		_row("18:06", "QUEUED"),
		object.union(_row("18:10", "ASSIGNED"), {"stallId": "A2"}),
		_row("18:16", "NO_SHOW"),
	]
	some v in ev_charging.violations with input as _msg("RESERVATION", ledger)
	startswith(v, "C2:")
}

test_c2_no_show_before_grace if {
	ledger := [
		object.union(_row("18:00", "ASSIGNED"), {"stallId": "A1"}),
		_row("18:06", "QUEUED"),
		object.union(_row("18:10", "ASSIGNED"), {"stallId": "A2"}),
		_row("18:16", "QUEUED"),
		object.union(_row("18:20", "ASSIGNED"), {"stallId": "A1"}),
		_row("18:23", "NO_SHOW"),
	]
	vs := ev_charging.violations with input as _msg("RESERVATION", ledger)
	count(vs) == 1
	some v in vs
	contains(v, "grace")
}

test_valid_no_show_forfeits_fee if {
	ledger := [
		object.union(_row("18:00", "ASSIGNED"), {"stallId": "A1"}),
		_row("18:06", "QUEUED"),
		object.union(_row("18:10", "ASSIGNED"), {"stallId": "A2"}),
		_row("18:16", "QUEUED"),
		object.union(_row("18:20", "ASSIGNED"), {"stallId": "A1"}),
		_row("18:26", "NO_SHOW"),
	]
	m := _msg("RESERVATION", ledger)
	count(ev_charging.violations) == 0 with input as m
	ev_charging.total_driver_payable == 100 with input as m
}
