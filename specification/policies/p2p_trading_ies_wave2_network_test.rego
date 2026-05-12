package deg.policy.p2p_trading_wave2_network

import rego.v1

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_base_context := {
	"networkId": "nfh.global/testnet-deg",
	"version": "2.0.0",
	"action": "on_status",
	"bapId": "bap.example.com",
	"bapUri": "http://beckn-router:9000/bap/receiver",
	"bppId": "bpp.example.com",
	"bppUri": "http://beckn-router:9000/bpp/caller",
	"transactionId": "txn-p2p-001",
	"messageId": "msg-001",
	"timestamp": "2026-04-26T06:30:00Z",
}

_base_participants := [
	{
		"role": "seller",
		"participantId": "TEST_SELLER_001",
		"participantAttributes": {
			"@type": "EnergyCustomer",
			"meterId": "TEST_METER_SELLER_001",
			"utilityId": "TEST_DISCOM_SELLER",
			"utilityCustomerId": "TEST_CUST_SELLER_001",
		},
	},
	{
		"role": "buyer",
		"participantId": "TEST_BUYER_001",
		"participantAttributes": {
			"@type": "EnergyCustomer",
			"meterId": "TEST_METER_BUYER_001",
			"utilityId": "TEST_DISCOM_BUYER",
			"utilityCustomerId": "TEST_CUST_BUYER_001",
		},
	},
	{
		"role": "buyerDiscom",
		"participantId": "buyer-discom-ledger",
		"participantAttributes": {
			"@type": "DiscomLedgerProvider",
			"utilityId": "TEST_DISCOM_BUYER",
			"ledgerUri": "http://beckn-router:9000/ledger/receiver",
		},
	},
	{
		"role": "sellerDiscom",
		"participantId": "seller-discom-ledger",
		"participantAttributes": {
			"@type": "DiscomLedgerProvider",
			"utilityId": "TEST_DISCOM_SELLER",
			"ledgerUri": "http://beckn-router:9000/ledger/receiver",
		},
	},
]

_base_contract_attributes := {
	"@type": "DEGContract",
	"roles": [
		{"role": "buyer", "participantId": "TEST_BUYER_001"},
		{"role": "seller", "participantId": "TEST_SELLER_001"},
		{"role": "buyerDiscom", "participantId": "buyer-discom-ledger"},
		{"role": "sellerDiscom", "participantId": "seller-discom-ledger"},
	],
}

_base_performance := [{
	"id": "perf-p2p-001",
	"status": {"code": "SETTLED", "name": "Settled: 2 intervals"},
	"commitmentIds": ["commitment-p2p-001"],
	"performanceAttributes": {
		"@type": "EnergyTradeDelivery",
		"deliveryStatus": "COMPLETED",
		"deliveryMode": "GRID_INJECTION",
		"performanceTimeseries": {
			"@type": "TimeSeries",
			"intervalPeriod": {"start": "2026-04-26T04:30:00Z", "duration": "PT1H"},
			"payloadDescriptors": [
				{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "BUYER_DISCOM_ALLOC", "units": "KWH"},
				{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "SELLER_DISCOM_ALLOC", "units": "KWH"},
				{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "BUYER_DISCOM_STATUS", "units": "STRING"},
				{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "SELLER_DISCOM_STATUS", "units": "STRING"},
				{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "FINAL_ALLOC", "units": "KWH"},
			],
			"intervals": [
				{"id": 0, "payloads": [
					{"type": "BUYER_DISCOM_ALLOC", "values": [18.5]},
					{"type": "SELLER_DISCOM_ALLOC", "values": [19.2]},
					{"type": "BUYER_DISCOM_STATUS", "values": ["COMPLETED"]},
					{"type": "SELLER_DISCOM_STATUS", "values": ["COMPLETED"]},
					{"type": "FINAL_ALLOC", "values": [18.5]},
				]},
				{"id": 1, "payloads": [
					{"type": "BUYER_DISCOM_ALLOC", "values": [14.2]},
					{"type": "SELLER_DISCOM_ALLOC", "values": [14.7]},
					{"type": "BUYER_DISCOM_STATUS", "values": ["COMPLETED"]},
					{"type": "SELLER_DISCOM_STATUS", "values": ["COMPLETED"]},
					{"type": "FINAL_ALLOC", "values": [14.2]},
				]},
			],
		},
	},
}]

_valid_on_status_input := {
	"context": _base_context,
	"message": {"contract": {
		"id": "contract-p2p-001",
		"status": {"code": "ACTIVE"},
		"contractAttributes": _base_contract_attributes,
		"performance": _base_performance,
		"participants": _base_participants,
	}},
}

# ---------------------------------------------------------------------------
# C1 — Version
# ---------------------------------------------------------------------------

test_c1_valid_version_pass if {
	count(violations) == 0 with input as _valid_on_status_input
}

test_c1_wrong_version_fail if {
	msgs := violations with input as json.patch(_valid_on_status_input, [{"op": "replace", "path": "/context/version", "value": "1.1.0"}])
	some msg in msgs
	contains(msg, "version")
	contains(msg, "1.1.0")
}

# ---------------------------------------------------------------------------
# C2 — Network ID
# ---------------------------------------------------------------------------

test_c2_valid_network_pass if {
	count([m | some m in violations; contains(m, "networkId")] ) == 0 with input as _valid_on_status_input
}

test_c2_unknown_network_fail if {
	msgs := violations with input as json.patch(_valid_on_status_input, [{"op": "replace", "path": "/context/networkId", "value": "unknown.net/fake"}])
	some msg in msgs
	contains(msg, "networkId")
	contains(msg, "unknown.net/fake")
}

# ---------------------------------------------------------------------------
# N1 — Required roles
# ---------------------------------------------------------------------------

test_n1_missing_role_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/contractAttributes/roles",
		"value": [
			{"role": "buyer", "participantId": "BRPL-buyer-001"},
			{"role": "seller", "participantId": "TPDDL-seller-001"},
		],
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "buyerDiscom")
}

# ---------------------------------------------------------------------------
# N2 — Participant utilityId non-empty
# ---------------------------------------------------------------------------

test_n2_empty_seller_utility_fail if {
	patched := json.patch(_valid_on_status_input, [{"op": "replace", "path": "/message/contract/participants/0/participantAttributes/utilityId", "value": ""}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "seller")
	contains(msg, "utilityId")
}

# ---------------------------------------------------------------------------
# N4 — Discom ledgerUri non-empty
# ---------------------------------------------------------------------------

test_n4_empty_buyer_discom_ledger_uri_fail if {
	patched := json.patch(_valid_on_status_input, [{"op": "replace", "path": "/message/contract/participants/2/participantAttributes/ledgerUri", "value": ""}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "buyerDiscom")
	contains(msg, "ledgerUri")
}

# ---------------------------------------------------------------------------
# N5 — No self-trade
# ---------------------------------------------------------------------------

test_n5_same_meter_fail if {
	patched := json.patch(_valid_on_status_input, [{"op": "replace", "path": "/message/contract/participants/1/participantAttributes/meterId", "value": "TEST_METER_SELLER_001"}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "same meterId")
}

# ---------------------------------------------------------------------------
# P1 — Required performance payload types
# ---------------------------------------------------------------------------

test_p1_missing_type_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/performance/0/performanceAttributes/performanceTimeseries/payloadDescriptors",
		"value": [
			{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "BUYER_DISCOM_ALLOC", "units": "KWH"},
			{"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "SELLER_DISCOM_ALLOC", "units": "KWH"},
		],
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "missing required types")
}

# ---------------------------------------------------------------------------
# P2 — Units
# ---------------------------------------------------------------------------

test_p2_wrong_alloc_units_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/performance/0/performanceAttributes/performanceTimeseries/payloadDescriptors/0",
		"value": {"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "BUYER_DISCOM_ALLOC", "units": "MWH"},
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "BUYER_DISCOM_ALLOC")
	contains(msg, "KWH")
}

test_p2_wrong_status_units_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/performance/0/performanceAttributes/performanceTimeseries/payloadDescriptors/2",
		"value": {"objectType": "REPORT_PAYLOAD_DESCRIPTOR", "payloadType": "BUYER_DISCOM_STATUS", "units": "KWH"},
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "BUYER_DISCOM_STATUS")
	contains(msg, "STRING")
}

# ---------------------------------------------------------------------------
# P3 — Interval duration
# ---------------------------------------------------------------------------

test_p3_wrong_duration_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/performance/0/performanceAttributes/performanceTimeseries/intervalPeriod/duration",
		"value": "PT30M",
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "duration")
	contains(msg, "PT1H")
}

# ---------------------------------------------------------------------------
# P4 — IST alignment (:30 UTC)
# ---------------------------------------------------------------------------

test_p4_correct_start_pass if {
	count([m | some m in violations; contains(m, "intervalPeriod.start")]) == 0 with input as _valid_on_status_input
}

test_p4_wrong_start_minute_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/performance/0/performanceAttributes/performanceTimeseries/intervalPeriod/start",
		"value": "2026-04-26T04:00:00Z",
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, ":30 UTC")
}

# ---------------------------------------------------------------------------
# P6 — DISCOM_STATUS enum
# ---------------------------------------------------------------------------

test_p6_invalid_status_code_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/performance/0/performanceAttributes/performanceTimeseries/intervals/0/payloads/2",
		"value": {"type": "BUYER_DISCOM_STATUS", "values": ["APPROVED"]},
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "APPROVED")
	contains(msg, "BUYER_DISCOM_STATUS")
}

test_p6_valid_status_codes_pass if {
	count([m | some m in violations; contains(m, "discom status code")]) == 0 with input as _valid_on_status_input
}

# ---------------------------------------------------------------------------
# P7 — FINAL_ALLOC ≤ min(BUYER_DISCOM_ALLOC, SELLER_DISCOM_ALLOC)
# ---------------------------------------------------------------------------

test_p7_final_alloc_exceeds_min_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/performance/0/performanceAttributes/performanceTimeseries/intervals/0/payloads/4",
		"value": {"type": "FINAL_ALLOC", "values": [25.0]},
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "FINAL_ALLOC")
	contains(msg, "interval 0")
}

test_p7_final_alloc_at_min_pass if {
	count([m | some m in violations; contains(m, "FINAL_ALLOC")]) == 0 with input as _valid_on_status_input
}

# ---------------------------------------------------------------------------
# T1 — Testnet mandatory TEST_ identifiers
# ---------------------------------------------------------------------------

# Base fixture is on testnet with TEST_ identifiers — should pass.
test_t1_testnet_all_test_prefixed_pass if {
	count([m | some m in violations with input as _valid_on_status_input; contains(m, "testnet:")]) == 0
}

# Testnet with a non-TEST_ utilityId → violation.
test_t1_testnet_non_test_utility_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/participants/0/participantAttributes/utilityId",
		"value": "TPDDL",
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "testnet:")
	contains(msg, "utilityId")
	contains(msg, "TEST_")
}

# Testnet with a non-TEST_ meterId → violation.
test_t1_testnet_non_test_meter_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/participants/0/participantAttributes/meterId",
		"value": "der://meter/real-seller-001",
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "testnet:")
	contains(msg, "meterId")
}

# Testnet with a non-TEST_ utilityCustomerId → violation.
test_t1_testnet_non_test_customer_fail if {
	patched := json.patch(_valid_on_status_input, [{
		"op": "replace",
		"path": "/message/contract/participants/0/participantAttributes/utilityCustomerId",
		"value": "REAL_CUST_001",
	}])
	msgs := violations with input as patched
	some msg in msgs
	contains(msg, "testnet:")
	contains(msg, "utilityCustomerId")
}

# ---------------------------------------------------------------------------
# T2 — Production allowlist (gated on production networkId)
# ---------------------------------------------------------------------------

# Production network with approved DISCOM utility IDs — should pass T2.
test_t2_prod_valid_utility_pass if {
	prod_input := json.patch(_valid_on_status_input, [
		{"op": "replace", "path": "/context/networkId", "value": "indiaenergystack.in/p2p-trading-ies-wave2"},
		{"op": "replace", "path": "/message/contract/participants/0/participantAttributes/utilityId", "value": "TPDDL"},
		{"op": "replace", "path": "/message/contract/participants/1/participantAttributes/utilityId", "value": "BRPL"},
	])
	count([m | some m in violations with input as prod_input; contains(m, "approved DISCOM")]) == 0
}

# Production network with unknown utility ID → T2 violation.
test_t2_prod_invalid_utility_fail if {
	prod_input := json.patch(_valid_on_status_input, [
		{"op": "replace", "path": "/context/networkId", "value": "indiaenergystack.in/p2p-trading-ies-wave2"},
		{"op": "replace", "path": "/message/contract/participants/0/participantAttributes/utilityId", "value": "FAKE_DISCOM"},
	])
	msgs := violations with input as prod_input
	some msg in msgs
	contains(msg, "approved DISCOM")
	contains(msg, "FAKE_DISCOM")
}
