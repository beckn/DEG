# Unit tests for demand_flex_revenue.rego role-based settlement
#
# Run:  cd specification/policies && opa test demand_flex_revenue.rego demand_flex_revenue_test.rego -v

package deg.contracts.demand_flex

import rego.v1

# ---------------------------------------------------------------------------
# Helper: build a mock contract payload with roles
# ---------------------------------------------------------------------------

_mock_input(offer_attrs, meters, event_window) := {
	"message": {"contract": {
		"id": "contract-flex-test",
		"status": {"code": "ACTIVE"},
		"participants": [
			{
				"id": "utility-test",
				"descriptor": {"name": "Test Utility"},
				"participantAttributes": {"@context": "test", "@type": "DEGParticipant", "role": "buyer"},
			},
			{
				"id": "aggregator-test",
				"descriptor": {"name": "Test Aggregator"},
				"participantAttributes": {"@context": "test", "@type": "DEGParticipant", "role": "seller"},
			},
		],
		"commitments": [{
			"id": "commitment-001",
			"status": {"descriptor": {"code": "ACTIVE"}},
			"resources": [{
				"id": "flex-need-test",
				"quantity": {"unitCode": "kW", "unitQuantity": 150},
				"resourceAttributes": {
					"@context": "test", "@type": "DemandFlexNeed",
					"direction": "REDUCE", "eventWindow": event_window,
					"capacityType": "CURTAILMENT", "maxCapacityKw": 500,
				},
			}],
			"offer": {
				"id": "offer-001",
				"resourceIds": ["flex-need-test"],
				"offerAttributes": offer_attrs,
			},
		}],
		"performance": [{"id": "perf-001", "status": {"code": "DELIVERY_COMPLETE"}, "commitmentIds": ["commitment-001"], "performanceAttributes": {
			"@context": "test", "@type": "DemandFlexPerformance",
			"eventId": "evt-test", "methodology": "5of10", "meters": meters,
		}}],
		"contractAttributes": {
			"@context": "test", "@type": "DEGContractPolicy",
			"policyUrl": "test", "queryPath": "test",
		},
	}},
}

_default_offer := {
	"@context": "test", "@type": "DemandFlexBuyOffer",
	"incentivePerKwh": 3.50, "currency": "INR",
	"penaltyRate": 1.50, "premiumForGuaranteed": 5.00, "optOutDefault": false,
}

_default_window := {"startDate": "2026-04-01T08:30:00Z", "endDate": "2026-04-01T10:30:00Z"}

# ---------------------------------------------------------------------------
# Test: happy path — revenue flows sum to zero
#
#   3 meters, 2h, 3.50 INR/kWh → total = 525
#   buyer: -525, seller: +525, sum = 0
# ---------------------------------------------------------------------------

test_revenue_flows_net_zero if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 20.0},
		{"meterId": "der://meter/002", "baselineKw": 38.0, "actualKw": 15.0},
		{"meterId": "der://meter/003", "baselineKw": 52.0, "actualKw": 25.0},
	], _default_window)

	flows := revenue_flows with input as inp
	count(flows) == 2

	# buyer pays
	some bf in flows
	bf.role == "buyer"
	bf.value == -525

	# seller receives
	some sf in flows
	sf.role == "seller"
	sf.value == 525

	# net-zero
	net_zero_ok with input as inp
	count(violations) == 0 with input as inp
}

# ---------------------------------------------------------------------------
# Test: roles extracted from participantAttributes
# ---------------------------------------------------------------------------

test_roles_detected if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 20.0},
	], _default_window)

	roles := _roles with input as inp
	"buyer" in roles
	"seller" in roles
}

# ---------------------------------------------------------------------------
# Test: missing role → violation
# ---------------------------------------------------------------------------

test_missing_seller_violation if {
	inp := {"message": {"contract": {
		"id": "test",
		"status": {"code": "ACTIVE"},
		"participants": [
			{"id": "u", "participantAttributes": {"@context": "t", "@type": "DEGParticipant", "role": "buyer"}},
		],
		"commitments": [_mock_input(_default_offer, [
			{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 20.0},
		], _default_window).message.contract.commitments[0]],
		"performance": [_mock_input(_default_offer, [
			{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 20.0},
		], _default_window).message.contract.performance[0]],
	}}}

	vs := violations with input as inp
	some v in vs
	contains(v, "seller")
}

# ---------------------------------------------------------------------------
# Test: settlement components correct
# ---------------------------------------------------------------------------

test_settlement_total if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 20.0},
		{"meterId": "der://meter/002", "baselineKw": 38.0, "actualKw": 15.0},
		{"meterId": "der://meter/003", "baselineKw": 52.0, "actualKw": 25.0},
	], _default_window)

	total_settlement == 525 with input as inp
	count(settlement_components) == 3 with input as inp
}

# ---------------------------------------------------------------------------
# Test: negative reduction clamped, no impact on revenue flows
# ---------------------------------------------------------------------------

test_clamped_meter_excluded if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 30.0, "actualKw": 40.0},
		{"meterId": "der://meter/002", "baselineKw": 50.0, "actualKw": 20.0},
	], _default_window)

	# meter/001 clamped to 0; meter/002: (50-20)*2*3.5 = 210
	total_settlement == 210 with input as inp

	flows := revenue_flows with input as inp
	some bf in flows
	bf.role == "buyer"
	bf.value == -210
}

# ---------------------------------------------------------------------------
# Test: 3-hour event scales revenue flows
# ---------------------------------------------------------------------------

test_3h_event if {
	window_3h := {"startDate": "2026-04-01T08:00:00Z", "endDate": "2026-04-01T11:00:00Z"}
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 40.0, "actualKw": 20.0},
	], window_3h)

	# (40-20)*3*3.5 = 210
	flows := revenue_flows with input as inp
	some sf in flows
	sf.role == "seller"
	sf.value == 210
}
