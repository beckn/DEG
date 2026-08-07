# Unit tests for demand-flex-contractpolicy.rego (per-interval, per-meter)
#
# Run:  cd specification/policies && opa test demand-flex-contractpolicy.rego test/demand-flex-contractpolicy_test.rego -v

package deg.contracts.demand_flex

import rego.v1

_ip := {"start": "2026-04-01T08:30:00Z", "duration": "PT30M"}

_need_ts := {
	"intervalPeriod": _ip,
	"payloadDescriptors": [
		{"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "CAPACITY_REQUESTED", "units": "KW", "insertedBy": "buyer"},
		{"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "PRICE", "units": "INR_PER_KWH", "insertedBy": "buyer"},
		{"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "SHORTFALL_PENALTY", "units": "INR_PER_KWH", "insertedBy": "buyer"},
	],
	"intervals": [
		{"id": 0, "payloads": [{"type": "CAPACITY_REQUESTED", "values": [150]}, {"type": "PRICE", "values": [3.5]}, {"type": "SHORTFALL_PENALTY", "values": [1.5]}]},
		{"id": 1, "payloads": [{"type": "CAPACITY_REQUESTED", "values": [200]}, {"type": "PRICE", "values": [4.0]}, {"type": "SHORTFALL_PENALTY", "values": [1.5]}]},
	],
}

_offered_ts := {
	"intervalPeriod": _ip,
	"payloadDescriptors": [{"objectType": "EVENT_PAYLOAD_DESCRIPTOR", "payloadType": "CAPACITY_OFFERED", "units": "KW", "insertedBy": "seller"}],
	"intervals": [
		{"id": 0, "payloads": [{"type": "CAPACITY_OFFERED", "values": [150]}]},
		{"id": 1, "payloads": [{"type": "CAPACITY_OFFERED", "values": [120]}]},
	],
}

_meter(id, b0, u0, b1, u1) := {
	"meterId": id,
	"telemetry": {
		"intervalPeriod": _ip,
		"payloadDescriptors": [
			{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "BASELINE", "units": "KW"},
			{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "USAGE", "units": "KW"},
		],
		"intervals": [
			{"id": 0, "payloads": [{"type": "BASELINE", "values": [b0]}, {"type": "USAGE", "values": [u0]}]},
			{"id": 1, "payloads": [{"type": "BASELINE", "values": [b1]}, {"type": "USAGE", "values": [u1]}]},
		],
	},
}

_mk(meters, offered, methodology) := {"message": {"contract": {
	"commitments": [{
		"resources": [{"id": "r1", "resourceAttributes": _need_ts}],
		"offer": {"offerAttributes": {"inputs": [
			{"role": "buyer", "inputs": {"currency": "INR", "baselineMethodology": {"bestOf": 5, "outOf": 10}}},
			{"role": "seller", "inputs": {"participatingMeters": ["m1"]}},
		]}},
		"commitmentAttributes": offered,
	}],
	"performance": [{"performanceAttributes": {"methodology": methodology, "meters": meters}}],
	"contractAttributes": {"roles": [{"role": "buyer"}, {"role": "seller"}]},
}}}

# meter m1: slot0 reduction 140, slot1 reduction 105
_std := _mk([_meter("m1", 150, 10, 200, 95)], _offered_ts, "5of10")

# slot0: min(140,150)=140 x0.5h x3.5 = 245; shortfall (150-140)=10 x0.5x1.5 = 7.5 -> 237.5
# slot1: min(105,120)=105 x0.5h x4.0 = 210; shortfall (120-105)=15 x0.5x1.5 = 11.25 -> 198.75
# total = 436.25
test_total_settlement if {
	total_settlement == 436.25 with input as _std
}

test_net_zero if {
	net_zero_ok with input as _std
}

test_revenue_flows if {
	rf := revenue_flows with input as _std
	some b in rf
	b.role == "buyer"
	b.value == -436.25
	some s in rf
	s.role == "seller"
	s.value == 436.25
}

test_two_line_items if {
	count(settlement_components) == 2 with input as _std
}

# two meters each delivering half -> same aggregate -> same total
test_per_meter_aggregation if {
	inp := _mk([_meter("m1", 75, 5, 100, 47.5), _meter("m2", 75, 5, 100, 47.5)], _offered_ts, "5of10")
	total_settlement == 436.25 with input as inp
}

# missing USAGE on a settled slot -> violation
test_missing_usage if {
	m := {"meterId": "m1", "telemetry": {"intervalPeriod": _ip, "payloadDescriptors": [], "intervals": [
		{"id": 0, "payloads": [{"type": "BASELINE", "values": [150]}]},
		{"id": 1, "payloads": [{"type": "BASELINE", "values": [200]}, {"type": "USAGE", "values": [95]}]},
	]}}
	vs := violations with input as _mk([m], _offered_ts, "5of10")
	some v in vs
	contains(v, "USAGE")
}

# RESOURCE_TELEMETRY-only payload -> excluded from settlement, explicit violation
test_resource_telemetry_only_excluded if {
	vs := violations with input as _mk([_meter("m1", 150, 10, 200, 95)], _offered_ts, "RESOURCE_TELEMETRY")
	some v in vs
	contains(v, "no settlement-eligible")
}

# Structural checks (column locks, CAPACITY_OFFERED presence/completeness/grid,
# meter-grid, roles) moved to the network policy — see
# test/demand-flex-networkpolicy_test.rego. This rego is settlement-only.

# revenue_flows is exported ONLY when a settlement-eligible performance record
# exists. This is what lets the contractpolicyenforcer step enforce `violations`
# pre-settlement while skipping injection (no zero-value settlement artifact on a
# confirm). Without performance the rule must be UNDEFINED.
test_revenue_flows_undefined_without_performance if {
	no_perf := json.patch(_std, [{"op": "remove", "path": "/message/contract/performance"}])
	not revenue_flows with input as no_perf
}

# with settlement performance present, revenue_flows is exported for injection
test_revenue_flows_defined_with_performance if {
	count(revenue_flows) == 2 with input as _std
}
