# DEG Network Policy — P2P Trading IES (wave2)
#
# Validates all beckn messages for the inter-discom P2P energy trading
# network. Rules are gated by message structure so they apply automatically
# to the relevant actions (on_select, init, on_status, …) without false
# positives on lighter payloads (discover, status ping, catalog/publish).
#
# ── common (all actions) ──
#
# C1. Version: context.version must be "2.0.0".
#
# ── contract validation (when message.contract exists) ──
#
# N1.  Required roles: buyer, seller, buyerDiscom, sellerDiscom must all be
#      present in contractAttributes.roles.
# N2.  Participant utilityIds: seller and buyer participants must each have a
#      non-empty utilityId.
# N3.  Inter-discom: buyer and seller must have different utilityIds.
# N4.  commitmentAttributes type: when commitmentAttributes is present it must
#      be @type: TimeSeries.
# N5.  commitmentAttributes payloadTypes: must declare PRICE_PER_KWH and
#      AVAILABLE_QTY when offer interval data is present.
# N6.  Offer currency: PRICE_PER_KWH descriptor must carry currency: INR.
# N7.  Offer qty units: AVAILABLE_QTY descriptor must carry units: KWH.
# N8.  Bid payloadTypes: must declare REQUESTED_QTY when bid interval data is
#      present (i.e. buyer has written at least one REQUESTED_QTY interval).
# N9.  Bid qty units: REQUESTED_QTY descriptor must carry units: KWH.
# N10. Interval id alignment: REQUESTED_QTY interval ids must be a subset of
#      AVAILABLE_QTY interval ids.
# N11. Quantity cap: REQUESTED_QTY ≤ AVAILABLE_QTY per matched interval.
# N12. No self-trade: buyer and seller meter ids must differ.
# N13. Seller source type must be a generation source (not GRID).
# N14. Seller payload: the seller offerAttributes.inputs entry must carry a
#      payload (BecknTimeSeries) — payloadDescriptors alone is not sufficient.
#
# ── performance validation (on_status with discom alloc in commitmentAttributes) ──
#
# P1.  payloadTypes declared: BUYER_DISCOM_ALLOC, SELLER_DISCOM_ALLOC, FINAL_ALLOC.
# P2.  Performance qty units: all three types must carry units: KWH.
# P3.  Interval coverage: BUYER_DISCOM_ALLOC interval ids must be a subset of
#      AVAILABLE_QTY interval ids.
# P4.  Settlement consistency: FINAL_ALLOC ≤ min(BUYER_DISCOM_ALLOC,
#      SELLER_DISCOM_ALLOC) per interval.
#
# ── TEST / PROD separation ──
#
# T1.  Production network: buyer and seller utilityIds must each be an
#      approved DISCOM (data.config.allowedUtilityIds or built-in default).
# T2.  Test consistency: if ANY buyer/seller participant uses a utilityId or
#      meterId that starts with "TEST_", ALL buyer/seller participants must
#      use TEST_ prefixed identifiers.
#
# Config:
#   data.config.productionNetworkIds  — set of production networkId strings
#   data.config.allowedUtilityIds     — set of approved DISCOM utilityIds
#   data.config.minDeliveryLeadHours  — not enforced here (interval-based
#                                       windows; enforce via catalog policy)

package deg.policy.p2p_trading_network

import rego.v1

# ---------------------------------------------------------------------------
# Config with defaults
# ---------------------------------------------------------------------------

_production_network_ids := {"beckn.one:deg:p2p-trading-ies:2.0.0"} if {
	not data.config.productionNetworkIds
} else := data.config.productionNetworkIds

_allowed_utility_ids := {"TPDDL-DL", "BRPL-DL", "PVVNL-DL", "BYPL-DL", "NDMC-DL"} if {
	not data.config.allowedUtilityIds
} else := data.config.allowedUtilityIds

# ---------------------------------------------------------------------------
# Timeseries helpers
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

# ---------------------------------------------------------------------------
# C1 — Version check (all actions)
# ---------------------------------------------------------------------------

_common_violations contains msg if {
	v := object.get(input.context, "version", "")
	v != "2.0.0"
	msg := sprintf("context.version is %q; must be 2.0.0", [v])
}

# ---------------------------------------------------------------------------
# Contract helpers
# ---------------------------------------------------------------------------

_contract := input.message.contract

_commitment := _contract.commitments[0]

_seller_role_inputs := [i | some i in _commitment.offer.offerAttributes.inputs; i.role == "seller"][0]

_buyer_role_inputs := [i | some i in _commitment.offer.offerAttributes.inputs; i.role == "buyer"][0]

_commit_ts := _commitment.commitmentAttributes

_commit_ts_types := _ts_types(_commit_ts) if {
	is_object(_commit_ts)
}

_offer_interval_ids := {i.id | some i in _commit_ts.intervals; some p in i.payloads; p.type == "AVAILABLE_QTY"}

_bid_interval_ids := {i.id | some i in _commit_ts.intervals; some p in i.payloads; p.type == "REQUESTED_QTY"}

_perf_interval_ids := {i.id | some i in _commit_ts.intervals; some p in i.payloads; p.type == "BUYER_DISCOM_ALLOC"}

_participant_by_role(role) := p if {
	some p in _contract.participants
	p.role == role
}

_seller_p := _participant_by_role("seller")

_buyer_p := _participant_by_role("buyer")

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
# N3 — Inter-discom: buyer and seller must be on different DISCOMs
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	_seller_p
	_buyer_p
	s_uid := _seller_p.participantAttributes.utilityId
	b_uid := _buyer_p.participantAttributes.utilityId
	s_uid == b_uid
	msg := sprintf(
		"seller and buyer have the same utilityId %q; inter-discom trade requires different DISCOMs",
		[s_uid],
	)
}

# ---------------------------------------------------------------------------
# N4 — commitmentAttributes with interval data must be @type: TimeSeries
# ---------------------------------------------------------------------------

_contract_violations contains "commitmentAttributes must have @type: TimeSeries" if {
	ca := _commitment.commitmentAttributes
	is_object(ca)
	ca.intervals  # only enforce when timeseries interval data is present
	ca["@type"] != "TimeSeries"
}

# ---------------------------------------------------------------------------
# N5-N7 — commitmentAttributes offer-side payloadType and unit validation
#          (only when offer interval data is present)
# ---------------------------------------------------------------------------

_contract_violations contains "commitmentAttributes payloadDescriptors must include PRICE_PER_KWH" if {
	is_object(_commit_ts)
	count(_offer_interval_ids) > 0
	not "PRICE_PER_KWH" in _commit_ts_types
}

_contract_violations contains "commitmentAttributes payloadDescriptors must include AVAILABLE_QTY" if {
	is_object(_commit_ts)
	count(_offer_interval_ids) > 0
	not "AVAILABLE_QTY" in _commit_ts_types
}

_contract_violations contains msg if {
	is_object(_commit_ts)
	"PRICE_PER_KWH" in _commit_ts_types
	c := _ts_currency(_commit_ts, "PRICE_PER_KWH")
	c != "INR"
	msg := sprintf("commitmentAttributes PRICE_PER_KWH currency is %q; must be INR", [c])
}

_contract_violations contains msg if {
	is_object(_commit_ts)
	"AVAILABLE_QTY" in _commit_ts_types
	u := _ts_units(_commit_ts, "AVAILABLE_QTY")
	u != "KWH"
	msg := sprintf("commitmentAttributes AVAILABLE_QTY units is %q; must be KWH", [u])
}

# ---------------------------------------------------------------------------
# N8-N9 — commitmentAttributes bid-side payloadType and unit validation
#          (only when buyer bid intervals are present)
# ---------------------------------------------------------------------------

_contract_violations contains "commitmentAttributes payloadDescriptors must include REQUESTED_QTY" if {
	is_object(_commit_ts)
	count(_bid_interval_ids) > 0
	not "REQUESTED_QTY" in _commit_ts_types
}

_contract_violations contains msg if {
	is_object(_commit_ts)
	"REQUESTED_QTY" in _commit_ts_types
	u := _ts_units(_commit_ts, "REQUESTED_QTY")
	u != "KWH"
	msg := sprintf("commitmentAttributes REQUESTED_QTY units is %q; must be KWH", [u])
}

# ---------------------------------------------------------------------------
# N10 — Interval id alignment: REQUESTED_QTY ids ⊆ AVAILABLE_QTY ids
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	is_object(_commit_ts)
	count(_bid_interval_ids) > 0
	count(_offer_interval_ids) > 0
	extra := _bid_interval_ids - _offer_interval_ids
	count(extra) > 0
	msg := sprintf(
		"commitmentAttributes REQUESTED_QTY interval ids %v not present in AVAILABLE_QTY interval ids %v",
		[extra, _offer_interval_ids],
	)
}

# ---------------------------------------------------------------------------
# N11 — REQUESTED_QTY ≤ AVAILABLE_QTY per interval
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	is_object(_commit_ts)
	some interval in _commit_ts.intervals
	interval.id in _offer_interval_ids
	interval.id in _bid_interval_ids
	req := _payload_val(interval, "REQUESTED_QTY")
	avail := _payload_val(interval, "AVAILABLE_QTY")
	req > avail
	msg := sprintf(
		"commitmentAttributes interval %v: REQUESTED_QTY %v kWh > AVAILABLE_QTY %v kWh",
		[interval.id, req, avail],
	)
}

# ---------------------------------------------------------------------------
# N12 — No self-trade: buyer and seller meter ids must differ
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
# N13 — Seller source type must be a generation source, not GRID
# ---------------------------------------------------------------------------

_contract_violations contains msg if {
	st := _commitment.resources[0].resourceAttributes.sourceType
	st == "GRID"
	msg := "seller sourceType is GRID; must be a generation source (SOLAR, BATTERY, HYBRID, RENEWABLE)"
}

# ---------------------------------------------------------------------------
# N14 — Seller role input must carry a payload (BecknTimeSeries with offer data)
# ---------------------------------------------------------------------------

_contract_violations contains "seller offerAttributes.inputs entry must carry a payload (BecknTimeSeries)" if {
	_seller_role_inputs
	not _seller_role_inputs.payload
}

# ---------------------------------------------------------------------------
# Performance validation (when BUYER_DISCOM_ALLOC present in commitmentAttributes)
# ---------------------------------------------------------------------------

_performance_violations contains "commitmentAttributes payloadDescriptors must include BUYER_DISCOM_ALLOC" if {
	is_object(_commit_ts)
	count(_perf_interval_ids) > 0
	not "BUYER_DISCOM_ALLOC" in _commit_ts_types
}

_performance_violations contains "commitmentAttributes payloadDescriptors must include SELLER_DISCOM_ALLOC" if {
	is_object(_commit_ts)
	count(_perf_interval_ids) > 0
	not "SELLER_DISCOM_ALLOC" in _commit_ts_types
}

_performance_violations contains "commitmentAttributes payloadDescriptors must include FINAL_ALLOC" if {
	is_object(_commit_ts)
	count(_perf_interval_ids) > 0
	not "FINAL_ALLOC" in _commit_ts_types
}

_performance_violations contains msg if {
	is_object(_commit_ts)
	some ptype in {"BUYER_DISCOM_ALLOC", "SELLER_DISCOM_ALLOC", "FINAL_ALLOC"}
	ptype in _commit_ts_types
	u := _ts_units(_commit_ts, ptype)
	u != "KWH"
	msg := sprintf("commitmentAttributes %v units is %q; must be KWH", [ptype, u])
}

_performance_violations contains msg if {
	is_object(_commit_ts)
	count(_perf_interval_ids) > 0
	extra := _perf_interval_ids - _offer_interval_ids
	count(extra) > 0
	msg := sprintf(
		"commitmentAttributes BUYER_DISCOM_ALLOC interval ids %v not present in AVAILABLE_QTY interval ids %v",
		[extra, _offer_interval_ids],
	)
}

_performance_violations contains msg if {
	is_object(_commit_ts)
	some interval in _commit_ts.intervals
	interval.id in _perf_interval_ids
	final_alloc := _payload_val(interval, "FINAL_ALLOC")
	buyer_alloc := _payload_val(interval, "BUYER_DISCOM_ALLOC")
	seller_alloc := _payload_val(interval, "SELLER_DISCOM_ALLOC")
	min_alloc := min({buyer_alloc, seller_alloc})
	final_alloc > min_alloc
	msg := sprintf(
		"commitmentAttributes interval %v: FINAL_ALLOC %v > min(BUYER_DISCOM_ALLOC %v, SELLER_DISCOM_ALLOC %v)",
		[interval.id, final_alloc, buyer_alloc, seller_alloc],
	)
}

# ---------------------------------------------------------------------------
# TEST / PROD separation
# ---------------------------------------------------------------------------

_is_production if input.context.networkId in _production_network_ids

# T1 — Production: buyer and seller utilityIds must be approved DISCOMs
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

# T2 — Test consistency: if any buyer/seller uses TEST_ prefix, all must
_any_is_test if {
	some p in _contract.participants
	p.role in {"buyer", "seller"}
	startswith(p.participantAttributes.utilityId, "TEST_")
}

_any_is_test if {
	some p in _contract.participants
	p.role in {"buyer", "seller"}
	startswith(p.participantAttributes.meterId, "TEST_")
}

_test_violations contains msg if {
	_any_is_test
	some p in _contract.participants
	p.role in {"buyer", "seller"}
	not startswith(p.participantAttributes.utilityId, "TEST_")
	msg := sprintf(
		"test consistency: participant %q (role: %s) utilityId %q must start with TEST_",
		[p.participantId, p.role, p.participantAttributes.utilityId],
	)
}

_test_violations contains msg if {
	_any_is_test
	some p in _contract.participants
	p.role in {"buyer", "seller"}
	not startswith(p.participantAttributes.meterId, "TEST_")
	msg := sprintf(
		"test consistency: participant %q (role: %s) meterId %q must start with TEST_",
		[p.participantId, p.role, p.participantAttributes.meterId],
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
	"BUYER_DISCOM_ALLOC" in _commit_ts_types
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
