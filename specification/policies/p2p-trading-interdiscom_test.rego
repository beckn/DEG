package deg.policy

import rego.v1

# ──────────────────────────────────────────────────────────────────────────────
# Helper – build a minimal input fragment for T1 / test-consistency tests.
# Only the fields read by _test_consistency_violations are populated; other
# rules (lead-time, @type/@context, etc.) are not exercised here.
# ──────────────────────────────────────────────────────────────────────────────

_input_with_ids(buyer_meter, buyer_utility, provider_meter, provider_utility) := {
	"context": {
		"version": "2.0.0",
		"action": "on_confirm",
		"timestamp": "2024-10-04T05:00:00Z",
		"domain": "beckn.one:deg:p2p-trading-interdiscom:2.0.0",
	},
	"message": {"order": {
		"beckn:buyer": {"beckn:buyerAttributes": {
			"meterId": buyer_meter,
			"utilityId": buyer_utility,
		}},
		"beckn:orderItems": [{"beckn:orderItemAttributes": {"providerAttributes": {
			"meterId": provider_meter,
			"utilityId": provider_utility,
		}}}],
	}},
}

# ──────────────────────────────────────────────────────────────────────────────
# T1 – test-consistency violation rules
# ──────────────────────────────────────────────────────────────────────────────

# All real IDs → no violations
test_t1_all_real_ids_pass if {
	count(_test_consistency_violations) == 0 with input as _input_with_ids(
		"REAL_METER_001", "PVVNL",
		"REAL_METER_002", "TPDDL",
	)
}

# All correct test IDs → no violations
test_t1_all_test_ids_pass if {
	count(_test_consistency_violations) == 0 with input as _input_with_ids(
		"TEST_METER_BUYER", "TEST_DISCOM_BUYER",
		"TEST_METER_SELLER", "TEST_DISCOM_SELLER",
	)
}

# Provider TEST_, buyer real → violation on buyer fields (original T1 direction)
test_t1_provider_test_buyer_real_fail if {
	msgs := _test_consistency_violations with input as _input_with_ids(
		"REAL_METER_001", "PVVNL",
		"TEST_METER_SELLER", "TEST_DISCOM_SELLER",
	)
	some msg in msgs
	contains(msg, "buyer meterId")
	contains(msg, "TEST_METER_BUYER")
}

# Buyer TEST_, provider real → violation on provider fields
# This is the case that was previously not caught (the bug fix).
# Reproduces the exact payload: buyer TEST_SELLER_METER + provider ABCD/PVVNL.
test_t1_buyer_test_provider_real_fail if {
	msgs := _test_consistency_violations with input as _input_with_ids(
		"TEST_SELLER_METER", "TEST_SELLER_DISCOM",
		"ABCD", "PVVNL",
	)
	some msg in msgs
	contains(msg, "provider meterId")
	contains(msg, "ABCD")
}

test_t1_buyer_test_provider_real_fail_utility if {
	msgs := _test_consistency_violations with input as _input_with_ids(
		"TEST_SELLER_METER", "TEST_SELLER_DISCOM",
		"ABCD", "PVVNL",
	)
	some msg in msgs
	contains(msg, "provider utilityId")
	contains(msg, "PVVNL")
}

# Buyer uses wrong test IDs (e.g. seller IDs instead of buyer IDs) → violation
test_t1_buyer_wrong_test_meter_fail if {
	msgs := _test_consistency_violations with input as _input_with_ids(
		"TEST_METER_SELLER", "TEST_DISCOM_BUYER",
		"TEST_METER_SELLER", "TEST_DISCOM_SELLER",
	)
	some msg in msgs
	contains(msg, "TEST_METER_BUYER")
}

# Only buyer utilityId is a real value while other fields are TEST_ → violation
test_t1_mixed_buyer_utility_fail if {
	msgs := _test_consistency_violations with input as _input_with_ids(
		"TEST_METER_BUYER", "PVVNL",
		"TEST_METER_SELLER", "TEST_DISCOM_SELLER",
	)
	some msg in msgs
	contains(msg, "buyer utilityId")
	contains(msg, "TEST_DISCOM_BUYER")
}
