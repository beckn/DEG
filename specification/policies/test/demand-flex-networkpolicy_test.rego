# Unit tests for demand-flex-networkpolicy.rego
#
# Run:  cd specification/policies && opa test demand-flex-networkpolicy.rego test/demand-flex-networkpolicy_test.rego -v

package deg.policy.demand_flex_network

import rego.v1

# Helper: minimal on_status payload with one meter
_payload(meter) := {"message": {"contract": {"performance": [{"performanceAttributes": {"meters": [meter]}}]}}}

# Test: clean payload (every used type declared) → no violations
test_clean_payload if {
	meter := {
		"meterId": "der://meter/001",
		"telemetry": {
			"payloadDescriptors": [
				{"payloadType": "BASELINE"},
				{"payloadType": "USAGE"},
			],
			"intervals": [{"payloads": [
				{"type": "BASELINE", "values": [46.0]},
				{"type": "USAGE", "values": [22.0]},
			]}],
		},
	}
	count(violations) == 0 with input as _payload(meter)
}

# Test: typo in interval (BASELIN instead of BASELINE) → violation
test_typo_baselin_in_interval if {
	meter := {
		"meterId": "der://meter/001",
		"telemetry": {
			"payloadDescriptors": [
				{"payloadType": "BASELINE"},
				{"payloadType": "USAGE"},
			],
			"intervals": [{"payloads": [
				{"type": "BASELIN", "values": [46.0]},
				{"type": "USAGE", "values": [22.0]},
			]}],
		},
	}
	vs := violations with input as _payload(meter)
	count(vs) == 1
	some v in vs
	contains(v, "BASELIN")
	contains(v, "der://meter/001")
}

# Test: declared-but-unused (USAGE in descriptors, only BASELINE in intervals) → no violation
test_declared_but_unused_is_allowed if {
	meter := {
		"meterId": "der://meter/001",
		"telemetry": {
			"payloadDescriptors": [
				{"payloadType": "BASELINE"},
				{"payloadType": "USAGE"},
			],
			"intervals": [{"payloads": [{"type": "BASELINE", "values": [46.0]}]}],
		},
	}
	count(violations) == 0 with input as _payload(meter)
}

# Test: action without telemetry (e.g. on_select) → no violation
test_no_performance_no_violation if {
	inp := {"message": {"contract": {"id": "c1"}}}
	count(violations) == 0 with input as inp
}

# Test: typo on one meter, others clean → exactly one violation, naming the bad meter
test_typo_isolated_to_one_meter if {
	good := {
		"meterId": "der://meter/002",
		"telemetry": {
			"payloadDescriptors": [{"payloadType": "BASELINE"}],
			"intervals": [{"payloads": [{"type": "BASELINE", "values": [40.0]}]}],
		},
	}
	bad := {
		"meterId": "der://meter/001",
		"telemetry": {
			"payloadDescriptors": [{"payloadType": "BASELINE"}],
			"intervals": [{"payloads": [{"type": "BASLN", "values": [46.0]}]}],
		},
	}
	inp := {"message": {"contract": {"performance": [{"performanceAttributes": {"meters": [good, bad]}}]}}}
	vs := violations with input as inp
	count(vs) == 1
	some v in vs
	contains(v, "der://meter/001")
	contains(v, "BASLN")
}

# ---------------------------------------------------------------------------
# 1b) DemandFlexNeed cross-field type-coverage (need is itself a TimeSeries)
# ---------------------------------------------------------------------------

_valid_need := {
	"intervalPeriod": {"start": "2026-04-01T08:30:00Z", "duration": "PT30M"},
	"payloadDescriptors": [
		{"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "CAPACITY_REQUESTED"},
		{"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "PRICE"},
		{"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "SHORTFALL_PENALTY"},
	],
	"intervals": [{"id": 0, "payloads": [{"type": "CAPACITY_REQUESTED", "values": [150]}, {"type": "PRICE", "values": [3.5]}, {"type": "SHORTFALL_PENALTY", "values": [1.5]}]}],
}

_need_input(ra) := {"message": {"contract": {"commitments": [{"resources": [{"resourceAttributes": ra}]}]}}}

# clean need → no violations
test_need_type_coverage_ok if {
	count(violations) == 0 with input as _need_input(_valid_need)
}

# undeclared payload type in the need → violation naming DemandFlexNeed + the type
test_need_type_coverage_violation if {
	bad := json.patch(_valid_need, [{"op": "add", "path": "/intervals/0/payloads/-", "value": {"type": "MYSTERY", "values": [1]}}])
	vs := violations with input as _need_input(bad)
	some v in vs
	contains(v, "DemandFlexNeed")
	contains(v, "MYSTERY")
}

# need missing payloadDescriptors → every used type flagged
test_need_missing_descriptors_violation if {
	bad := json.patch(_valid_need, [{"op": "remove", "path": "/payloadDescriptors"}])
	vs := violations with input as _need_input(bad)
	some v in vs
	contains(v, "DemandFlexNeed")
}

# same check applies at catalog publish time
test_need_type_coverage_catalog if {
	bad := json.patch(_valid_need, [{"op": "add", "path": "/intervals/0/payloads/-", "value": {"type": "MYSTERY", "values": [1]}}])
	inp := {"message": {"catalogs": [{"resources": [{"resourceAttributes": bad}]}]}}
	vs := violations with input as inp
	some v in vs
	contains(v, "MYSTERY")
}

# ---------------------------------------------------------------------------
# 3) commitment formation completeness (fail fast at init/confirm)
# ---------------------------------------------------------------------------

# two-slot need + matching-grid CAPACITY_OFFERED series
_need2 := {
	"intervalPeriod": {"start": "2026-04-01T08:30:00Z", "duration": "PT30M"},
	"payloadDescriptors": [
		{"payloadType": "CAPACITY_REQUESTED"},
		{"payloadType": "PRICE"},
		{"payloadType": "SHORTFALL_PENALTY"},
	],
	"intervals": [
		{"id": 0, "payloads": [{"type": "CAPACITY_REQUESTED", "values": [150]}, {"type": "PRICE", "values": [3.5]}, {"type": "SHORTFALL_PENALTY", "values": [1.5]}]},
		{"id": 1, "payloads": [{"type": "CAPACITY_REQUESTED", "values": [200]}, {"type": "PRICE", "values": [4.0]}, {"type": "SHORTFALL_PENALTY", "values": [1.5]}]},
	],
}

_offered2 := {
	"@type": "TimeSeries",
	"intervalPeriod": {"start": "2026-04-01T08:30:00Z", "duration": "PT30M"},
	"payloadDescriptors": [{"payloadType": "CAPACITY_OFFERED"}],
	"intervals": [
		{"id": 0, "payloads": [{"type": "CAPACITY_OFFERED", "values": [150]}]},
		{"id": 1, "payloads": [{"type": "CAPACITY_OFFERED", "values": [120]}]},
	],
}

_commit_input(need, ca) := {"message": {"contract": {"commitments": [{
	"id": "cmt-1",
	"resources": [{"resourceAttributes": need}],
	"commitmentAttributes": ca,
}]}}}

# complete offer against every slot, matching grid → no violation
test_capacity_offered_complete_ok if {
	count(violations) == 0 with input as _commit_input(_need2, _offered2)
}

# offered series missing a slot → violation naming the missing interval
test_capacity_offered_missing_slot if {
	partial := json.patch(_offered2, [{"op": "remove", "path": "/intervals/1"}])
	vs := violations with input as _commit_input(_need2, partial)
	count(vs) == 1
	some v in vs
	contains(v, "missing CAPACITY_OFFERED")
	contains(v, "interval 1")
}

# offered grid does not match the need grid → violation
test_capacity_offered_grid_mismatch if {
	mism := json.patch(_offered2, [{"op": "replace", "path": "/intervalPeriod/duration", "value": "PT60M"}])
	vs := violations with input as _commit_input(_need2, mism)
	count(vs) == 1
	some v in vs
	contains(v, "does not match the DemandFlexNeed grid")
}

# no offered series yet (e.g. on_select) → formation checks self-skip
test_no_offer_yet_self_skips if {
	inp := {"message": {"contract": {"commitments": [{
		"id": "cmt-1",
		"resources": [{"resourceAttributes": _need2}],
		"status": {"descriptor": {"code": "ACTIVE"}},
	}]}}}
	count(violations) == 0 with input as inp
}

# ---------------------------------------------------------------------------
# 3a) CAPACITY_OFFERED column presence (stage-gated)
# ---------------------------------------------------------------------------

# commitment carrying a need but no commitmentAttributes at all, at a
# post-commitment action, adds the action + context envelope.
_need_only_at(action) := {"context": {"action": action}, "message": {"contract": {"commitments": [{
	"id": "cmt-1",
	"resources": [{"resourceAttributes": _need2}],
}]}}}

# whole CAPACITY_OFFERED column dropped at confirm → violation (the reported bug)
test_offer_column_dropped_at_confirm if {
	vs := violations with input as _need_only_at("confirm")
	some v in vs
	contains(v, "requires a CAPACITY_OFFERED column")
	contains(v, "confirm")
}

# same drop at init → violation
test_offer_column_dropped_at_init if {
	vs := violations with input as _need_only_at("init")
	some v in vs
	contains(v, "requires a CAPACITY_OFFERED column")
}

# same drop at on_status → violation
test_offer_column_dropped_at_status if {
	vs := violations with input as _need_only_at("on_status")
	some v in vs
	contains(v, "requires a CAPACITY_OFFERED column")
}

# select carries a bare need with no seller offer yet → must NOT flag
test_offer_column_absent_at_select_ok if {
	count(violations) == 0 with input as _need_only_at("select")
}

# full column present at confirm → no presence violation
test_offer_column_present_at_confirm_ok if {
	inp := object.union(_commit_input(_need2, _offered2), {"context": {"action": "confirm"}})
	count(violations) == 0 with input as inp
}

# ---------------------------------------------------------------------------
# 4) BecknTimeSeries interval id sequence
# ---------------------------------------------------------------------------

# ids 0,1 → no violation
test_interval_ids_ok if {
	count(violations) == 0 with input as _need_input(_need2)
}

# ids do not start at 0 → violation
test_interval_ids_must_start_at_zero if {
	bad := json.patch(_valid_need, [{"op": "replace", "path": "/intervals/0/id", "value": 1}])
	vs := violations with input as _need_input(bad)
	some v in vs
	contains(v, "DemandFlexNeed")
	contains(v, "start at 0")
}

# gap in ids (0,2) → violation
test_interval_ids_gap if {
	bad := json.patch(_need2, [{"op": "replace", "path": "/intervals/1/id", "value": 2}])
	vs := violations with input as _need_input(bad)
	some v in vs
	contains(v, "start at 0 and increase by 1")
}

# some intervals carry no id → violation (partial id declaration)
test_interval_ids_partial_missing if {
	bad := json.patch(_need2, [{"op": "remove", "path": "/intervals/1/id"}])
	vs := violations with input as _need_input(bad)
	some v in vs
	contains(v, "increase by 1")
}

# the id check also applies to the CAPACITY_OFFERED series
test_interval_ids_on_offered_series if {
	bad := json.patch(_offered2, [{"op": "replace", "path": "/intervals/0/id", "value": 5}])
	vs := violations with input as _commit_input(_need2, bad)
	some v in vs
	contains(v, "CAPACITY_OFFERED series")
}

# ---------------------------------------------------------------------------
# 5) column locks, roles & grid alignment (consolidated from the contract rego)
# ---------------------------------------------------------------------------

# 5a) roles — contractAttributes present but missing 'seller' → violation
test_roles_missing_seller if {
	inp := {"message": {"contract": {
		"contractAttributes": {"roles": [{"role": "buyer"}]},
		"commitments": [{"id": "cmt-1", "resources": [{"resourceAttributes": _need2}]}],
	}}}
	vs := violations with input as inp
	some v in vs
	contains(v, "role 'seller'")
}

# 5a) both roles present, well-formed offer → no violation
test_roles_present_ok if {
	inp := {"message": {"contract": {
		"contractAttributes": {"roles": [{"role": "buyer"}, {"role": "seller"}]},
		"commitments": [{"id": "cmt-1", "resources": [{"resourceAttributes": _need2}], "commitmentAttributes": _offered2}],
	}}}
	count(violations) == 0 with input as inp
}

# 5a) no contractAttributes (discover / catalog) → self-skips
test_roles_self_skip_without_contract_attributes if {
	count(violations) == 0 with input as _payload({
		"meterId": "der://meter/001",
		"telemetry": {"payloadDescriptors": [{"payloadType": "BASELINE"}], "intervals": [{"payloads": [{"type": "BASELINE", "values": [1]}]}]},
	})
}

# 5b) DemandFlexNeed carrying an extra column → violation
test_need_column_lock_violation if {
	extra := json.patch(_need2, [{"op": "add", "path": "/payloadDescriptors/-", "value": {"payloadType": "EXTRA"}}])
	vs := violations with input as _commit_input(extra, _offered2)
	some v in vs
	contains(v, "DemandFlexNeed columns must be exactly")
}

# 5c) commitment column declared as something other than CAPACITY_OFFERED → violation
test_offered_column_lock_violation if {
	bad := json.patch(_offered2, [{"op": "replace", "path": "/payloadDescriptors/0/payloadType", "value": "CAPACITY_PROMISED"}])
	vs := violations with input as _commit_input(_need2, bad)
	some v in vs
	contains(v, "must be exactly {CAPACITY_OFFERED}")
}

# 5d) meter telemetry grid does not match the need grid → violation
test_meter_grid_mismatch if {
	meter := {"meterId": "m1", "telemetry": {
		"intervalPeriod": {"start": "2026-04-01T08:30:00Z", "duration": "PT60M"},
		"payloadDescriptors": [{"payloadType": "BASELINE"}, {"payloadType": "USAGE"}],
		"intervals": [{"id": 0, "payloads": [{"type": "BASELINE", "values": [46]}, {"type": "USAGE", "values": [22]}]}],
	}}
	inp := {"message": {"contract": {
		"commitments": [{"id": "cmt-1", "resources": [{"resourceAttributes": _need2}], "commitmentAttributes": _offered2}],
		"performance": [{"performanceAttributes": {"meters": [meter]}}],
	}}}
	vs := violations with input as inp
	some v in vs
	contains(v, "telemetry intervalPeriod does not match")
}
