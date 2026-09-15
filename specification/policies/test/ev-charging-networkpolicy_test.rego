package deg.policy.ev_charging_network_test

import rego.v1

import data.deg.policy.ev_charging_network as network

_terms := {"currency": "INR", "energyPerKWh": 18, "occupancyPerMin": 2, "idlePerMin": 10, "graceMin": 5, "maxDemotions": 2, "gridDelayCreditPerMin": 1, "reservation": {"fee": 100, "cancelBeforeMin": 60, "cpoDelayCreditPerMin": 5, "liabilityCap": 500}}

_roles := [{"role": "cpo", "participantId": "bpp.example.com"}, {"role": "driver", "participantId": "bap.example.com"}]

_row(at, state) := {"at": sprintf("2026-10-02T%v:00Z", [at]), "state": state}

_ledger := [
	_row("12:05", "QUEUED"),
	object.union(_row("18:12", "ASSIGNED"), {"stallId": "A1"}),
	object.union(_row("18:15", "CHARGING"), {"kWh": 10.0}),
	object.union(_row("18:25", "LIMITED_BY_GRID"), {"kWh": 5.0, "eventId": "DR-1"}),
	_row("18:55", "IDLE"),
	_row("19:04", "DEPARTED"),
]

_msg(action, timestamp, status, ledger) := {"context": {"action": action, "timestamp": timestamp}, "message": {"contract": object.union(
	{
		"status": {"code": status},
		"commitments": [{
			"offer": {"id": "reserve", "offerAttributes": {"@type": "ChargingOffer", "mode": "RESERVATION", "terms": _terms}},
			"commitmentAttributes": {"vehicle": {"maxChargeKW": 60}, "reservedStart": "2026-10-02T18:00:00Z", "quote": {"promisedKW": 60}},
		}],
		"contractAttributes": {"roles": _roles},
	},
	_performance(ledger),
)}}

_performance(ledger) := {} if ledger == null

_performance(ledger) := {"performance": [{"performanceAttributes": {"@type": "ChargingSession", "ledger": ledger}}]} if ledger != null

_settled := _msg("on_status", "2026-10-02T19:05:00Z", "COMPLETE", _ledger)

_has(vs, prefix) if {
	some v in vs
	startswith(v, prefix)
}

test_valid_settled_message if {
	count(network.violations) == 0 with input as _settled
}

test_valid_select_without_ledger if {
	count(network.violations) == 0 with input as _msg("select", "2026-10-02T12:00:00Z", "DRAFT", null)
}

test_n1_driver_unbound if {
	m := json.patch(_msg("init", "2026-10-02T12:00:00Z", "DRAFT", null), [{"op": "replace", "path": "/message/contract/contractAttributes/roles/1/participantId", "value": null}])
	_has(network.violations, "N1:") with input as m
}

test_n1_extra_role if {
	m := json.patch(_settled, [{"op": "add", "path": "/message/contract/contractAttributes/roles/-", "value": {"role": "network", "participantId": "x"}}])
	_has(network.violations, "N1:") with input as m
}

test_n2_walk_in_with_reservation_terms if {
	m := json.patch(_settled, [{"op": "replace", "path": "/message/contract/commitments/0/offer/offerAttributes/mode", "value": "WALK_IN"}])
	_has(network.violations, "N2: offer reserve is WALK_IN") with input as m
}

test_n2_reservation_without_reserved_start if {
	m := json.patch(_settled, [{"op": "remove", "path": "/message/contract/commitments/0/commitmentAttributes/reservedStart"}])
	_has(network.violations, "N2: commitment") with input as m
}

test_n3_reservation_too_soon if {
	_has(network.violations, "N3:") with input as _msg("select", "2026-10-02T17:20:00Z", "DRAFT", null)
}

test_n3_not_applied_after_confirm if {
	not _has(network.violations, "N3:") with input as _settled
}

test_n4_promise_above_vehicle_limit if {
	m := json.patch(_settled, [{"op": "replace", "path": "/message/contract/commitments/0/commitmentAttributes/quote/promisedKW", "value": 80}])
	_has(network.violations, "N4:") with input as m
}

test_n5_illegal_transition if {
	ledger := [_row("12:05", "QUEUED"), object.union(_row("18:15", "CHARGING"), {"kWh": 1}), _row("18:20", "DEPARTED")]
	_has(network.violations, "N5: illegal transition QUEUED -> CHARGING") with input as _msg("on_status", "2026-10-02T19:05:00Z", "COMPLETE", ledger)
}

test_n5_row_after_terminal if {
	ledger := array.concat(_ledger, [_row("19:10", "QUEUED")])
	_has(network.violations, "N5: illegal transition DEPARTED -> QUEUED") with input as _msg("on_status", "2026-10-02T19:15:00Z", "ACTIVE", ledger)
}

test_n5_time_not_increasing if {
	m := json.patch(_settled, [{"op": "replace", "path": "/message/contract/performance/0/performanceAttributes/ledger/2/at", "value": "2026-10-02T18:10:00Z"}])
	_has(network.violations, "N5: ledger row 2") with input as m
}

test_n6_missing_event_id if {
	m := json.patch(_settled, [{"op": "remove", "path": "/message/contract/performance/0/performanceAttributes/ledger/3/eventId"}])
	_has(network.violations, "N6: ledger row 3 (LIMITED_BY_GRID) requires eventId") with input as m
}

test_n6_energy_on_idle if {
	m := json.patch(_settled, [{"op": "add", "path": "/message/contract/performance/0/performanceAttributes/ledger/4/kWh", "value": 1}])
	_has(network.violations, "N6: ledger row 4 (IDLE) must not carry kWh") with input as m
}

test_n7_implausible_power if {
	m := json.patch(_settled, [{"op": "replace", "path": "/message/contract/performance/0/performanceAttributes/ledger/2/kWh", "value": 20}])
	_has(network.violations, "N7:") with input as m
}

test_n8_status_mismatch if {
	m := json.patch(_settled, [{"op": "replace", "path": "/message/contract/status/code", "value": "ACTIVE"}])
	_has(network.violations, "N8:") with input as m
}
