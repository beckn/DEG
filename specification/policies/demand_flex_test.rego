# Unit tests for demand_flex.rego settlement computation
#
# Run:  cd specification/policies && opa test . -v

package deg.contracts.demand_flex

import rego.v1

# ---------------------------------------------------------------------------
# Helper: build a mock on_status input
# ---------------------------------------------------------------------------

_mock_input(offer_attrs, meters, event_window) := {
	"message": {"contract": {
		"id": "contract-flex-test",
		"status": {"code": "ACTIVE"},
		"commitments": [{
			"id": "commitment-flex-001",
			"status": {"descriptor": {"code": "ACTIVE"}},
			"resources": [{
				"id": "flex-need-test",
				"quantity": {"unitCode": "kW", "unitQuantity": 150},
				"resourceAttributes": {
					"@context": "test",
					"@type": "DemandFlexNeed",
					"direction": "REDUCE",
					"eventWindow": event_window,
					"capacityType": "CURTAILMENT",
					"maxCapacityKw": 500,
				},
			}],
			"offer": {
				"id": "offer-flex-001",
				"resourceIds": ["flex-need-test"],
				"offerAttributes": offer_attrs,
			},
		}],
		"performance": [{"id": "perf-001", "status": {"code": "DELIVERY_COMPLETE"}, "commitmentIds": ["commitment-flex-001"], "performanceAttributes": {
			"@context": "test",
			"@type": "DemandFlexPerformance",
			"eventId": "evt-test",
			"methodology": "5of10",
			"meters": meters,
		}}],
		"contractAttributes": {"@context": "test", "@type": "DEGContract", "contractType": "DEMAND_FLEX"},
	}},
}

_default_offer := {
	"@context": "test",
	"@type": "DemandFlexBuyOffer",
	"incentivePerKwh": 3.50,
	"currency": "INR",
	"penaltyRate": 1.50,
	"premiumForGuaranteed": 5.00,
	"optOutDefault": false,
	"policy": {"url": "test", "queryPath": "test"},
}

_default_window := {
	"startDate": "2026-04-01T08:30:00Z",
	"endDate": "2026-04-01T10:30:00Z",
}

# ---------------------------------------------------------------------------
# Test: happy path — 3 meters, 2h event, 3.50 INR/kWh
#
#   meter/001: (45-20)=25 kW × 2h = 50 kWh × 3.50 = 175.00
#   meter/002: (38-15)=23 kW × 2h = 46 kWh × 3.50 = 161.00
#   meter/003: (52-25)=27 kW × 2h = 54 kWh × 3.50 = 189.00
#   total = 525.00
# ---------------------------------------------------------------------------

test_happy_path_settlement if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 20.0},
		{"meterId": "der://meter/002", "baselineKw": 38.0, "actualKw": 15.0},
		{"meterId": "der://meter/003", "baselineKw": 52.0, "actualKw": 25.0},
	], _default_window)

	total_settlement == 525.0 with input as inp
	count(settlement_components) == 3 with input as inp
	net_zero_ok with input as inp
	count(violations) == 0 with input as inp
}

# ---------------------------------------------------------------------------
# Test: missing actualKw on one meter → violation + excluded from total
# ---------------------------------------------------------------------------

test_missing_actuals_violation if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 20.0},
		{"meterId": "der://meter/002", "baselineKw": 38.0},
	], _default_window)

	# Only meter/001 counted  → (45-20)*2*3.5 = 175
	total_settlement == 175.0 with input as inp
	count(settlement_components) == 1 with input as inp

	# Violation for the missing meter
	vs := violations with input as inp
	count(vs) == 1
	some v in vs
	contains(v, "meter/002")
	contains(v, "missing actualKw")
}

# ---------------------------------------------------------------------------
# Test: actual > baseline → clamped to zero + warning violation
# ---------------------------------------------------------------------------

test_negative_reduction_clamped if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 30.0, "actualKw": 40.0},
		{"meterId": "der://meter/002", "baselineKw": 50.0, "actualKw": 20.0},
	], _default_window)

	# meter/001: clamped to 0.  meter/002: (50-20)*2*3.5 = 210
	total_settlement == 210.0 with input as inp

	vs := violations with input as inp
	some v in vs
	contains(v, "meter/001")
	contains(v, "clamped to zero")
}

# ---------------------------------------------------------------------------
# Test: 3-hour event window scales correctly
# ---------------------------------------------------------------------------

test_event_hours_3h if {
	window_3h := {
		"startDate": "2026-04-01T08:00:00Z",
		"endDate": "2026-04-01T11:00:00Z",
	}
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 40.0, "actualKw": 20.0},
	], window_3h)

	event_hours == 3 with input as inp
	# (40-20)*3*3.5 = 210
	total_settlement == 210.0 with input as inp
}

# ---------------------------------------------------------------------------
# Test: single meter, minimal case
# ---------------------------------------------------------------------------

test_single_meter if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 100.0, "actualKw": 60.0},
	], _default_window)

	# (100-60)*2*3.5 = 280
	total_settlement == 280.0 with input as inp
	count(settlement_components) == 1 with input as inp
}

# ---------------------------------------------------------------------------
# Test: zero reduction (actual == baseline) → zero payout, no violation
# ---------------------------------------------------------------------------

test_zero_reduction if {
	inp := _mock_input(_default_offer, [
		{"meterId": "der://meter/001", "baselineKw": 45.0, "actualKw": 45.0},
	], _default_window)

	total_settlement == 0 with input as inp
	count(violations) == 0 with input as inp
}
