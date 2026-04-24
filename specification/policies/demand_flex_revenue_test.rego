# Unit tests for demand_flex_revenue.rego role-based settlement
#
# Run:  cd specification/policies && opa test demand_flex_revenue.rego demand_flex_revenue_test.rego -v

package deg.contracts.demand_flex

import rego.v1

# ---------------------------------------------------------------------------
# Helper: build a mock contract payload
# ---------------------------------------------------------------------------

_deg_contract := {
	"@context": "test", "@type": "DEGContract",
	"roles": [{"role": "buyer"}, {"role": "seller"}],
	"policy": {"url": "test", "queryPath": "test"},
}

_default_inputs := [
	{"role": "buyer", "participantId": "utility-test", "inputs": {
		"incentivePerKwh": 3.50,
		"currency": "INR",
		"penaltyRate": 1.50,
		"premiumForGuaranteed": 5.00,
		"maxEventsPerMonth": 5,
		"baselineMethodology": {"bestOf": 5, "outOf": 10},
		"optOutDefault": false,
	}},
	{"role": "seller", "participantId": "agg-test", "inputs": {
		"plannedDemandChange": 150.0,
		"participatingMeters": ["m1", "m2", "m3"],
	}},
]

_default_window := {"startDate": "2026-04-01T08:30:00Z", "endDate": "2026-04-01T10:30:00Z"}

_mock_input(role_inputs, meters, event_window, contract_attrs) := {
	"message": {"contract": {
		"id": "test",
		"status": {"code": "ACTIVE"},
		"commitments": [{
			"id": "c1",
			"status": {"descriptor": {"code": "ACTIVE"}},
			"resources": [{
				"id": "r1",
				"quantity": {"unitCode": "kW", "unitQuantity": 150},
				"resourceAttributes": {
					"@context": "test", "@type": "DemandFlexNeed",
					"direction": "REDUCE", "eventWindow": event_window,
					"capacityType": "CURTAILMENT", "maxCapacityKw": 500,
				},
			}],
			"offer": {
				"id": "o1", "resourceIds": ["r1"],
				"offerAttributes": {
					"@context": "test", "@type": "DemandFlexBuyOffer",
					"inputs": role_inputs,
				},
			},
		}],
		"performance": [{"id": "p1", "status": {"code": "DELIVERY_COMPLETE"}, "commitmentIds": ["c1"], "performanceAttributes": {
			"@context": "test", "@type": "DemandFlexPerformance",
			"eventId": "evt-test", "methodology": "5of10", "meters": meters,
		}}],
		"contractAttributes": contract_attrs,
	}},
}

_std_input(meters) := _mock_input(_default_inputs, meters, _default_window, _deg_contract)

# ---------------------------------------------------------------------------
# Test: happy path — revenue flows sum to zero
# ---------------------------------------------------------------------------

test_revenue_flows_net_zero if {
	inp := _std_input([
		{"meterId": "m1", "baselineKw": 45.0, "actualKw": 20.0},
		{"meterId": "m2", "baselineKw": 38.0, "actualKw": 15.0},
		{"meterId": "m3", "baselineKw": 52.0, "actualKw": 25.0},
	])

	flows := revenue_flows with input as inp
	count(flows) == 2

	some bf in flows; bf.role == "buyer"; bf.value == -525
	some sf in flows; sf.role == "seller"; sf.value == 525

	net_zero_ok with input as inp
	count(violations) == 0 with input as inp
}

# ---------------------------------------------------------------------------
# Test: roles extracted from contractAttributes
# ---------------------------------------------------------------------------

test_roles_detected if {
	inp := _std_input([{"meterId": "m1", "baselineKw": 45.0, "actualKw": 20.0}])
	roles := _roles with input as inp
	"buyer" in roles
	"seller" in roles
}

# ---------------------------------------------------------------------------
# Test: missing role → violation
# ---------------------------------------------------------------------------

test_missing_seller_violation if {
	no_seller := {"@context": "test", "@type": "DEGContract", "roles": [{"role": "buyer"}], "policy": {"url": "t", "queryPath": "t"}}
	inp := _mock_input(_default_inputs, [{"meterId": "m1", "baselineKw": 45.0, "actualKw": 20.0}], _default_window, no_seller)
	vs := violations with input as inp
	some v in vs
	contains(v, "seller")
}

# ---------------------------------------------------------------------------
# Test: settlement total
# ---------------------------------------------------------------------------

test_settlement_total if {
	inp := _std_input([
		{"meterId": "m1", "baselineKw": 45.0, "actualKw": 20.0},
		{"meterId": "m2", "baselineKw": 38.0, "actualKw": 15.0},
		{"meterId": "m3", "baselineKw": 52.0, "actualKw": 25.0},
	])
	total_settlement == 525 with input as inp
	count(settlement_components) == 3 with input as inp
}

# ---------------------------------------------------------------------------
# Test: negative reduction clamped
# ---------------------------------------------------------------------------

test_clamped_meter_excluded if {
	inp := _std_input([
		{"meterId": "m1", "baselineKw": 30.0, "actualKw": 40.0},
		{"meterId": "m2", "baselineKw": 50.0, "actualKw": 20.0},
	])
	total_settlement == 210 with input as inp
	flows := revenue_flows with input as inp
	some bf in flows; bf.role == "buyer"; bf.value == -210
}

# ---------------------------------------------------------------------------
# Test: 3-hour event scales
# ---------------------------------------------------------------------------

test_3h_event if {
	w3h := {"startDate": "2026-04-01T08:00:00Z", "endDate": "2026-04-01T11:00:00Z"}
	inp := _mock_input(_default_inputs, [{"meterId": "m1", "baselineKw": 40.0, "actualKw": 20.0}], w3h, _deg_contract)
	flows := revenue_flows with input as inp
	some sf in flows; sf.role == "seller"; sf.value == 210
}
