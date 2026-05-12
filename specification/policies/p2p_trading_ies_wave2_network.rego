# DEG Network Policy — P2P Trading IES wave2
#
# Validates beckn messages for inter-discom P2P energy trading (wave2).
# Rules are gated on message structure and fire only on relevant actions.
#
# ── common (all actions) ──
#
# C1.  Version: context.version must be "2.0.0".
# C2.  Network: context.networkId must be in the allowed set.
#
# ── contract validation (when message.contract exists) ──
#
# N1.  Required roles: buyer, seller, buyerDiscom, sellerDiscom.
# N2.  Participant utilityIds: buyer and seller must have non-empty utilityId.
# N4.  Discom ledgerUri: buyerDiscom and sellerDiscom must have non-empty ledgerUri.
# N5.  No self-trade: buyer and seller meterIds must differ.
# N6.  offerTimeseries payloadTypes: PRICE_PER_KWH and AVAILABLE_QTY required.
# N7.  Offer currency: PRICE_PER_KWH must have currency INR.
# N8.  Offer qty units: AVAILABLE_QTY must have units KWH.
# N9.  bidTimeseries payloadTypes: REQUESTED_QTY required.
# N10. Bid qty units: REQUESTED_QTY must have units KWH.
# N11. Interval id alignment: bid interval ids must be a subset of offer ids.
# N12. Quantity cap: REQUESTED_QTY ≤ AVAILABLE_QTY per matched interval.
# N13. Seller source type must not be GRID.
#
# ── booking validation (confirm / on_confirm) ──
#
# P5.  Lead time: context.timestamp must be at least 4 hours before delivery start.
#
# ── performance validation (on_status with performanceTimeseries) ──
#
# P1.  Required payload types: BUYER_DISCOM_ALLOC, SELLER_DISCOM_ALLOC,
#      BUYER_DISCOM_STATUS, SELLER_DISCOM_STATUS, FINAL_ALLOC.
# P2.  Units: *_ALLOC types → KWH; *_STATUS types → STRING.
# P3.  Interval duration: intervalPeriod.duration must be "PT1H".
# P4.  IST alignment: intervalPeriod.start must be at :30 UTC (≡ 00:00 IST).
# P6.  DISCOM_STATUS enum: each interval value must be one of the allowed codes.
# P7.  Settlement cap: FINAL_ALLOC ≤ min(BUYER_DISCOM_ALLOC, SELLER_DISCOM_ALLOC)
#      per interval.
#
# ── TEST / PROD separation ──
#
# T1.  Testnet mandatory: when networkId is the test network, ALL buyer/seller
#      utilityIds, meterIds, utilityCustomerIds, and discom utilityIds must start
#      with "TEST_".
# T2.  Production allowlist: when networkId is a production network, buyer and
#      seller utilityIds must be approved DISCOMs.
#
# Config:
#   data.config.productionNetworkIds  — set of production networkId strings
#   data.config.allowedUtilityIds     — set of approved DISCOM utilityIds
#   data.config.allowedNetworkIds     — set of all permitted network IDs

package deg.policy.p2p_trading_wave2_network

import rego.v1

# ---------------------------------------------------------------------------
# Config with defaults
# ---------------------------------------------------------------------------

_allowed_network_ids := {
	"nfh.global/testnet-deg",
	"indiaenergystack.in/p2p-trading-ies-wave2",
} if {
	not data.config.allowedNetworkIds
} else := data.config.allowedNetworkIds

_production_network_ids := {"indiaenergystack.in/p2p-trading-ies-wave2"} if {
	not data.config.productionNetworkIds
} else := data.config.productionNetworkIds

_allowed_utility_ids := {"TPDDL", "BRPL", "PVVNL"} if {
	not data.config.allowedUtilityIds
} else := data.config.allowedUtilityIds

_valid_discom_status_codes := {
	"PENDING",
	"CONFIRMED",
	"CANCELLED_OUTAGE",
	"CANCELLED_POL_VIOLATION",
	"CURTAILED_OUTAGE",
	"CURTAILED_POL_VIOLATION",
	"COMPLETED",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ts_types(ts) := {d.payloadType | some d in ts.payloadDescriptors}

_ts_units(ts, ptype) := u if {
	some d in ts.payloadDescriptors
	d.payloadType == ptype
	u := d.units
}

_ts_currency(ts, ptype) := c if {
	some d in ts.payloadDescriptors
	d.payloadType == ptype
	c := d.currency
}

_payload_val(interval, ptype) := v if {
	some p in interval.payloads
	p.type == ptype
	v := p.values[0]
}

# Returns nanoseconds elapsed within the current UTC hour for an RFC-3339 string.
_nanos_within_hour(iso_str) := ns if {
	epoch_ns := time.parse_rfc3339_ns(iso_str)
	ns := epoch_ns % (3600 * 1000000000)
}

# ---------------------------------------------------------------------------
# C1 — Version (all actions)
# ---------------------------------------------------------------------------

_common_violations contains msg if {
	v := object.get(input.context, "version", "")
	v != "2.0.0"
	msg := sprintf("context.version is %q; must be 2.0.0", [v])
}

# ---------------------------------------------------------------------------
# C2 — Network ID (all actions)
# ---------------------------------------------------------------------------

_common_violations contains msg if {
	nid := object.get(input.context, "networkId", "")
	not nid in _allowed_network_ids
	msg := sprintf("context.networkId %q is not in the allowed network set %v", [nid, _allowed_network_ids])
}

# ---------------------------------------------------------------------------
# Contract helpers
# ---------------------------------------------------------------------------

_contract := input.message.contract

_commitment := _contract.commitments[0]

_seller_role_inputs := [i | some i in _commitment.offer.offerAttributes.inputs; i.role == "seller"][0]

_buyer_role_inputs := [i | some i in _commitment.offer.offerAttributes.inputs; i.role == "buyer"][0]

_offer_ts := _seller_role_inputs.inputs.offerTimeseries

_bid_ts := _buyer_role_inputs.inputs.bidTimeseries

_offer_interval_ids := {i.id | some i in _offer_ts.intervals}

_participant_by_role(role) := p if {
	some p in _contract.participants
	p.role == role
}

_seller_p := _participant_by_role("seller")

_buyer_p := _participant_by_role("buyer")

_buyer_discom_p := _participant_by_role("buyerDiscom")

_seller_discom_p := _participant_by_role("sellerDiscom")

# ---------------------------------------------------------------------------
# N1 — Required roles
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	required := {"buyer", "seller", "buyerDiscom", "sellerDiscom"}
	roles_present := {r.role | some r in _contract.contractAttributes.roles}
	missing := required - roles_present
	count(missing) > 0
	msg := sprintf("missing required role(s) in contractAttributes.roles: %v", [missing])
}

# ---------------------------------------------------------------------------
# N2 — Participant utilityIds non-empty
# ---------------------------------------------------------------------------

_contract_violations contains "seller participant utilityId is missing or empty" if {
	_seller_p
	uid := object.get(_seller_p.participantAttributes, "utilityId", "")
	uid == ""
}

_contract_violations contains "buyer participant utilityId is missing or empty" if {
	_buyer_p
	uid := object.get(_buyer_p.participantAttributes, "utilityId", "")
	uid == ""
}

# ---------------------------------------------------------------------------
# N4 — Discom ledgerUri non-empty
# ---------------------------------------------------------------------------

_contract_violations contains "buyerDiscom participant ledgerUri is missing or empty" if {
	_buyer_discom_p
	uri := object.get(_buyer_discom_p.participantAttributes, "ledgerUri", "")
	uri == ""
}

_contract_violations contains "sellerDiscom participant ledgerUri is missing or empty" if {
	_seller_discom_p
	uri := object.get(_seller_discom_p.participantAttributes, "ledgerUri", "")
	uri == ""
}

# ---------------------------------------------------------------------------
# N5 — No self-trade
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	_seller_p
	_buyer_p
	s_mid := _seller_p.participantAttributes.meterId
	b_mid := _buyer_p.participantAttributes.meterId
	s_mid == b_mid
	msg := sprintf(
		"seller and buyer have the same meterId %q; a prosumer cannot self-trade",
		[s_mid],
	)
}

# ---------------------------------------------------------------------------
# N6-N8 — offerTimeseries payload types and units
# ---------------------------------------------------------------------------

_contract_violations contains "seller offerTimeseries payloadDescriptors must include PRICE_PER_KWH" if {
	_offer_ts
	not "PRICE_PER_KWH" in _ts_types(_offer_ts)
}

_contract_violations contains "seller offerTimeseries payloadDescriptors must include AVAILABLE_QTY" if {
	_offer_ts
	not "AVAILABLE_QTY" in _ts_types(_offer_ts)
}

_contract_violations contains msg if {
	_offer_ts
	"PRICE_PER_KWH" in _ts_types(_offer_ts)
	c := _ts_currency(_offer_ts, "PRICE_PER_KWH")
	c != "INR"
	msg := sprintf("offerTimeseries PRICE_PER_KWH currency is %q; must be INR", [c])
}

_contract_violations contains msg if {
	_offer_ts
	"AVAILABLE_QTY" in _ts_types(_offer_ts)
	u := _ts_units(_offer_ts, "AVAILABLE_QTY")
	u != "KWH"
	msg := sprintf("offerTimeseries AVAILABLE_QTY units is %q; must be KWH", [u])
}

# ---------------------------------------------------------------------------
# N9-N10 — bidTimeseries payload type and units
# ---------------------------------------------------------------------------

_contract_violations contains "buyer bidTimeseries payloadDescriptors must include REQUESTED_QTY" if {
	_bid_ts
	not "REQUESTED_QTY" in _ts_types(_bid_ts)
}

_contract_violations contains msg if {
	_bid_ts
	"REQUESTED_QTY" in _ts_types(_bid_ts)
	u := _ts_units(_bid_ts, "REQUESTED_QTY")
	u != "KWH"
	msg := sprintf("bidTimeseries REQUESTED_QTY units is %q; must be KWH", [u])
}

# ---------------------------------------------------------------------------
# N11 — Interval id alignment: bid ids ⊆ offer ids
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	_bid_ts
	_offer_ts
	bid_ids := {i.id | some i in _bid_ts.intervals}
	extra := bid_ids - _offer_interval_ids
	count(extra) > 0
	msg := sprintf(
		"buyer bidTimeseries interval ids %v not present in seller offerTimeseries ids %v",
		[extra, _offer_interval_ids],
	)
}

# ---------------------------------------------------------------------------
# N12 — REQUESTED_QTY ≤ AVAILABLE_QTY per interval
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	_bid_ts
	_offer_ts
	some bi in _bid_ts.intervals
	bi.id in _offer_interval_ids
	req := _payload_val(bi, "REQUESTED_QTY")
	some oi in _offer_ts.intervals
	oi.id == bi.id
	avail := _payload_val(oi, "AVAILABLE_QTY")
	req > avail
	msg := sprintf(
		"bid interval %v: REQUESTED_QTY %v kWh > seller AVAILABLE_QTY %v kWh",
		[bi.id, req, avail],
	)
}

# ---------------------------------------------------------------------------
# N13 — Seller source type must not be GRID
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	st := _seller_role_inputs.inputs.sourceType
	st == "GRID"
	msg := "seller sourceType is GRID; must be a generation source (SOLAR, BATTERY, HYBRID, RENEWABLE)"
}

# ---------------------------------------------------------------------------
# P5 — Booking lead time (confirm / on_confirm only)
# ---------------------------------------------------------------------------

_booking_violations contains msg if {
	input.context.action in {"confirm", "on_confirm"}
	_offer_ts.intervalPeriod.start
	msg_ns := time.parse_rfc3339_ns(input.context.timestamp)
	del_ns := time.parse_rfc3339_ns(_offer_ts.intervalPeriod.start)
	del_ns - msg_ns < 4 * 60 * 60 * 1000000000
	msg := sprintf(
		"booking timestamp %q is less than 4 hours before delivery start %q; minimum lead time is 4 hours",
		[input.context.timestamp, _offer_ts.intervalPeriod.start],
	)
}

# ---------------------------------------------------------------------------
# Performance helpers (on_status)
# ---------------------------------------------------------------------------

_perf := _contract.performance[0]

_perf_ts := _perf.performanceAttributes.performanceTimeseries

# ---------------------------------------------------------------------------
# P1 — Required performance payload types
# ---------------------------------------------------------------------------

_required_perf_types := {
	"BUYER_DISCOM_ALLOC",
	"SELLER_DISCOM_ALLOC",
	"BUYER_DISCOM_STATUS",
	"SELLER_DISCOM_STATUS",
	"FINAL_ALLOC",
}

_performance_violations contains msg if {
	_perf_ts
	missing := _required_perf_types - _ts_types(_perf_ts)
	count(missing) > 0
	msg := sprintf("performance timeseries payloadDescriptors missing required types: %v", [missing])
}

# ---------------------------------------------------------------------------
# P2 — Units per payload type
# ---------------------------------------------------------------------------

_performance_violations contains msg if {
	_perf_ts
	some ptype in {"BUYER_DISCOM_ALLOC", "SELLER_DISCOM_ALLOC", "FINAL_ALLOC"}
	ptype in _ts_types(_perf_ts)
	u := _ts_units(_perf_ts, ptype)
	u != "KWH"
	msg := sprintf("performance timeseries %v units is %q; must be KWH", [ptype, u])
}

_performance_violations contains msg if {
	_perf_ts
	some ptype in {"BUYER_DISCOM_STATUS", "SELLER_DISCOM_STATUS"}
	ptype in _ts_types(_perf_ts)
	u := _ts_units(_perf_ts, ptype)
	u != "STRING"
	msg := sprintf("performance timeseries %v units is %q; must be STRING", [ptype, u])
}

# ---------------------------------------------------------------------------
# P3 — Interval duration must be PT1H
# ---------------------------------------------------------------------------

_performance_violations contains msg if {
	_perf_ts.intervalPeriod
	dur := object.get(_perf_ts.intervalPeriod, "duration", "")
	dur != "PT1H"
	msg := sprintf("performanceTimeseries intervalPeriod.duration is %q; must be PT1H (1 hour)", [dur])
}

# ---------------------------------------------------------------------------
# P4 — IST alignment: intervalPeriod.start must be at :30 UTC (= 00:00 IST)
# ---------------------------------------------------------------------------

_performance_violations contains msg if {
	_perf_ts.intervalPeriod.start
	start := _perf_ts.intervalPeriod.start
	ns_within_hour := _nanos_within_hour(start)
	ns_within_hour != 30 * 60 * 1000000000
	msg := sprintf(
		"performanceTimeseries intervalPeriod.start %q must begin at :30 UTC (00:00 IST)",
		[start],
	)
}

# ---------------------------------------------------------------------------
# P6 — DISCOM_STATUS enum per interval
# ---------------------------------------------------------------------------

_performance_violations contains msg if {
	_perf_ts
	some pi in _perf_ts.intervals
	some status_type in {"BUYER_DISCOM_STATUS", "SELLER_DISCOM_STATUS"}
	v := _payload_val(pi, status_type)
	not v in _valid_discom_status_codes
	msg := sprintf(
		"performance interval %v: %v value %q is not a valid discom status code; must be one of %v",
		[pi.id, status_type, v, _valid_discom_status_codes],
	)
}

# ---------------------------------------------------------------------------
# P7 — FINAL_ALLOC ≤ min(BUYER_DISCOM_ALLOC, SELLER_DISCOM_ALLOC) per interval
# ---------------------------------------------------------------------------

_performance_violations contains msg if {
	_perf_ts
	some pi in _perf_ts.intervals
	final_alloc := _payload_val(pi, "FINAL_ALLOC")
	buyer_alloc := _payload_val(pi, "BUYER_DISCOM_ALLOC")
	seller_alloc := _payload_val(pi, "SELLER_DISCOM_ALLOC")
	min_alloc := min({buyer_alloc, seller_alloc})
	final_alloc > min_alloc
	msg := sprintf(
		"performance interval %v: FINAL_ALLOC %v > min(BUYER_DISCOM_ALLOC %v, SELLER_DISCOM_ALLOC %v)",
		[pi.id, final_alloc, buyer_alloc, seller_alloc],
	)
}

# ---------------------------------------------------------------------------
# TEST / PROD separation
# ---------------------------------------------------------------------------

_is_production if input.context.networkId in _production_network_ids

_is_testnet if input.context.networkId == "nfh.global/testnet-deg"

# T1 — Testnet mandatory: on the test network every regulated identifier must carry a TEST_ prefix.
_test_violations contains msg if {
	_is_testnet
	some p in _contract.participants
	p.role in {"buyer", "seller", "buyerDiscom", "sellerDiscom"}
	uid := object.get(p.participantAttributes, "utilityId", "")
	uid != ""
	not startswith(uid, "TEST_")
	msg := sprintf(
		"testnet: participant %q (role: %s) utilityId %q must start with TEST_",
		[p.participantId, p.role, uid],
	)
}

_test_violations contains msg if {
	_is_testnet
	some p in _contract.participants
	p.role in {"buyer", "seller"}
	mid := object.get(p.participantAttributes, "meterId", "")
	mid != ""
	not startswith(mid, "TEST_")
	msg := sprintf(
		"testnet: participant %q (role: %s) meterId %q must start with TEST_",
		[p.participantId, p.role, mid],
	)
}

_test_violations contains msg if {
	_is_testnet
	some p in _contract.participants
	p.role in {"buyer", "seller"}
	cid := object.get(p.participantAttributes, "utilityCustomerId", "")
	cid != ""
	not startswith(cid, "TEST_")
	msg := sprintf(
		"testnet: participant %q (role: %s) utilityCustomerId %q must start with TEST_",
		[p.participantId, p.role, cid],
	)
}

# T2 — Production allowlist: utilityIds must be approved DISCOMs on production networks.
_prod_violations contains msg if {
	_is_production
	some p in _contract.participants
	p.role in {"buyer", "seller"}
	uid := p.participantAttributes.utilityId
	not uid in _allowed_utility_ids
	msg := sprintf(
		"participant %q (role: %s): utilityId %q is not an approved DISCOM; must be one of %v",
		[p.participantId, p.role, uid, _allowed_utility_ids],
	)
}

# ---------------------------------------------------------------------------
# Public violations API
# ---------------------------------------------------------------------------

violations contains msg if {
	some msg in _common_violations
}

violations contains msg if {
	input.message.contract
	some msg in _contract_violations
}

violations contains msg if {
	input.message.contract
	some msg in _booking_violations
}

violations contains msg if {
	input.message.contract
	input.context.action == "on_status"
	some msg in _performance_violations
}

violations contains msg if {
	input.message.contract
	some msg in _prod_violations
}

violations contains msg if {
	input.message.contract
	some msg in _test_violations
}
