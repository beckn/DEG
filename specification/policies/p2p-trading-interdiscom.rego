package deg.policy

import rego.v1

# P2P Energy Trading – Delivery, Validity & Meter Policy
#
# Rules are gated by message structure so they automatically apply to
# all beckn actions: confirm, on_confirm, select, on_select, init,
# on_init, status, on_status, update, on_update, catalog_publish.
#
# ── common (all actions) ──
#
# C1. Domain: context.domain must be "beckn.one:deg:p2p-trading-interdiscom:2.0.0".
# C2. Version: context.version must be "2.0.0".
#
# ── order validation (when message.order exists) ──
#
# O1. Delivery lead time: delivery window start must be at least
#     minDeliveryLeadHours after the trade timestamp (context.timestamp).
# O2. Validity-to-delivery gap: validity window end must be at least
#     minDeliveryLeadHours before delivery window start.
# O3. Delivery slot duration: delivery window must be exactly 1 hour.
# O4. Meter ID validation:
#     a. Buyer meterId must not be empty.
#     b. Buyer meterId must differ from each order item's provider meterId.
# O5. Quantity bounds: beckn:quantity.unitQuantity must be >= 0 and strictly
#     less than the offer's applicableQuantity.unitQuantity.
# O6. Currency: schema:priceCurrency must be "INR".
# O7. Quantity unit: beckn:quantity.unitText must be "kWh".
# O8. EnergyCustomer required fields: utilityCustomerId and utilityId must be
#     present and non-empty on both buyer and provider.
# O9. EnergyCustomer @type: beckn:buyerAttributes.@type and
#     providerAttributes.@type must be "EnergyCustomer".
# O10. EnergyCustomer @context: when @type is "EnergyCustomer", @context must
#      match the P2P energy trading JSON-LD context URL.
# O11. EnergyTradeOrder @context: when order @type is "EnergyTradeOrder",
#      @context must match the same URL.
# O12. EnergyTradeOffer @context: when offer @type is "EnergyTradeOffer",
#      @context must match the same URL.
#
# ── catalog_publish action (catalog item & offer validation) ──
#
# P1. Production network items: beckn:providerAttributes must exist, utilityId
#     must be an approved DISCOM (TPDDL, PVVNL, BRPL).
# P2. Non-production network items: provider meterId must be TEST_METER_SELLER,
#     provider utilityId must be TEST_DISCOM_SELLER.
# P3. Validity-to-delivery gap: on each catalog offer, validity window end must
#     be at least minDeliveryLeadHours before delivery window start (mirrors O2).
# P3b. [DISABLED] Delivery slot duration: delivery window must be exactly 1 hour
#      (mirrors O3).
# P4. Currency: each catalog offer's schema:priceCurrency must be "INR" (mirrors O6).
# P5. Quantity unit: each catalog offer's applicableQuantity.unitText must be
#     "kWh" (mirrors O7).
# P6. Provider utilityCustomerId must be present and non-empty (mirrors O8).
# P7. Provider utilityId must be present and non-empty (mirrors O8).
# P8. Provider @type must be "EnergyCustomer" (mirrors O9).
# P9. Provider EnergyCustomer @context must match the P2P energy trading
#     JSON-LD context URL (mirrors O10).
# P10. EnergyTradeOffer @context: when offerAttributes @type is
#      "EnergyTradeOffer", @context must match the same URL (mirrors O12).
#
# ── test ID consistency (when message.order exists) ──
#
# T1. If ANY party (buyer OR any provider) uses a test identifier (meterId
#     or utilityId starting with "TEST_"), ALL parties must use test values:
#       buyer    → meterId = TEST_METER_BUYER, utilityId = TEST_DISCOM_BUYER
#       provider → meterId and utilityId must each start with "TEST_"
#
# Config:
#   data.config.minDeliveryLeadHours  - minimum hours of lead time (default: 4)

default min_lead_hours := 4

min_lead_hours := to_number(data.config.minDeliveryLeadHours) if {
	data.config.minDeliveryLeadHours
}

ns_per_hour := 1000 * 1000 * 1000 * 60 * 60

# Parse the trade timestamp from context
trade_time := time.parse_rfc3339_ns(input.context.timestamp)

# Helper: resolve delivery window from either field name convention
_delivery_window(offer_attrs) := object.get(offer_attrs, "deliveryWindow", object.get(offer_attrs, "beckn:timeWindow", null))

# Helper: resolve validity window from either field name convention
_validity_window(offer_attrs) := object.get(offer_attrs, "validityWindow", object.get(offer_attrs, "beckn:validityWindow", null))

# Rule 13 – Domain must match the P2P inter-DISCOM trading profile
_required_domain := "beckn.one:deg:p2p-trading-interdiscom:2.0.0"

_common_violations contains msg if {
	input.context.domain
	input.context.domain != _required_domain

	msg := sprintf(
		"context.domain is %q; must be %q",
		[input.context.domain, _required_domain],
	)
}

_common_violations contains msg if {
	not input.context.domain

	msg := sprintf(
		"context.domain is missing; must be %q",
		[_required_domain],
	)
}

# Rule 14 – Version must be 2.0.0
_required_version := "2.0.0"

_common_violations contains msg if {
	input.context.version
	input.context.version != _required_version

	msg := sprintf(
		"context.version is %q; must be %q",
		[input.context.version, _required_version],
	)
}

_common_violations contains msg if {
	not input.context.version

	msg := sprintf(
		"context.version is missing; must be %q",
		[_required_version],
	)
}

# Rule 1 – Delivery lead time
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	offer_attrs := item["beckn:acceptedOffer"]["beckn:offerAttributes"]

	dw := _delivery_window(offer_attrs)
	dw != null

	start_str := dw["schema:startTime"]
	delivery_start := time.parse_rfc3339_ns(start_str)

	lead_hours := (delivery_start - trade_time) / ns_per_hour
	lead_hours < min_lead_hours

	msg := sprintf(
		"order item [%d]: delivery window start (%s) is only %v hours after trade time (%s); minimum is %v hours",
		[i, start_str, lead_hours, input.context.timestamp, min_lead_hours],
	)
}

# Rule 2 – Validity window must end at least minDeliveryLeadHours before delivery start
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	offer_attrs := item["beckn:acceptedOffer"]["beckn:offerAttributes"]

	dw := _delivery_window(offer_attrs)
	dw != null
	vw := _validity_window(offer_attrs)
	vw != null

	delivery_start := time.parse_rfc3339_ns(dw["schema:startTime"])
	validity_end_str := vw["schema:endTime"]
	validity_end := time.parse_rfc3339_ns(validity_end_str)

	gap_hours := (delivery_start - validity_end) / ns_per_hour
	gap_hours < min_lead_hours

	msg := sprintf(
		"order item [%d]: validity window end (%s) is only %v hours before delivery start; minimum gap is %v hours",
		[i, validity_end_str, gap_hours, min_lead_hours],
	)
}

# Rule 3 – Delivery window must be exactly 1 hour
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	offer_attrs := item["beckn:acceptedOffer"]["beckn:offerAttributes"]

	dw := _delivery_window(offer_attrs)
	dw != null

	start_str := dw["schema:startTime"]
	end_str := dw["schema:endTime"]
	duration_hours := (time.parse_rfc3339_ns(end_str) - time.parse_rfc3339_ns(start_str)) / ns_per_hour

	duration_hours != 1

	msg := sprintf(
		"order item [%d]: delivery window (%s to %s) is %v hours; must be exactly 1 hour",
		[i, start_str, end_str, duration_hours],
	)
}

# Helper: extract buyer meterId
_buyer_meter_id := input.message.order["beckn:buyer"]["beckn:buyerAttributes"].meterId

# Rule 4a – Buyer meterId must not be empty
_order_violations contains "buyer meterId is missing or empty" if {
	not _buyer_meter_id
}

_order_violations contains "buyer meterId is missing or empty" if {
	_buyer_meter_id == ""
}

# Rule 4b – Buyer meterId must differ from provider meterId on each order item
_order_violations contains msg if {
	buyer_mid := _buyer_meter_id
	buyer_mid != ""

	item := input.message.order["beckn:orderItems"][i]
	provider_mid := item["beckn:orderItemAttributes"].providerAttributes.meterId

	buyer_mid == provider_mid

	msg := sprintf(
		"order item [%d]: buyer meterId (%s) is the same as provider meterId; a prosumer cannot trade with themselves",
		[i, buyer_mid],
	)
}


# Rule 6a – Ordered quantity must be >= 0
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	qty := item["beckn:quantity"].unitQuantity
	qty < 0

	msg := sprintf(
		"order item [%d]: beckn:quantity.unitQuantity is %v; must be >= 0",
		[i, qty],
	)
}

# Rule 6b – Ordered quantity must be < applicableQuantity (offer cap)
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	qty := item["beckn:quantity"].unitQuantity
	cap := item["beckn:acceptedOffer"]["beckn:price"].applicableQuantity.unitQuantity
	qty > cap

	msg := sprintf(
		"order item [%d]: beckn:quantity.unitQuantity (%v) must not be greater than the applicableQuantity (%v)",
		[i, qty, cap],
	)
}

# Rule 7 – Currency must be INR
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	currency := item["beckn:acceptedOffer"]["beckn:price"]["schema:priceCurrency"]
	currency != "INR"

	msg := sprintf(
		"order item [%d]: schema:priceCurrency is %q; must be INR",
		[i, currency],
	)
}

# Rule 8 – Quantity unit must be kWh
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	unit := item["beckn:quantity"].unitText
	unit != "kWh"

	msg := sprintf(
		"order item [%d]: beckn:quantity.unitText is %q; must be kWh",
		[i, unit],
	)
}

# Rule 9a – Buyer utilityCustomerId must be present and non-empty
_buyer_utility_cust_id := input.message.order["beckn:buyer"]["beckn:buyerAttributes"].utilityCustomerId

_order_violations contains "buyer utilityCustomerId is missing or empty" if {
	not _buyer_utility_cust_id
}

_order_violations contains "buyer utilityCustomerId is missing or empty" if {
	_buyer_utility_cust_id == ""
}

# Rule 9b – Provider utilityCustomerId must be present and non-empty per order item
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	not provider.utilityCustomerId

	msg := sprintf(
		"order item [%d]: provider utilityCustomerId is missing",
		[i],
	)
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	provider.utilityCustomerId == ""

	msg := sprintf(
		"order item [%d]: provider utilityCustomerId is empty",
		[i],
	)
}

# Rule 9c – Buyer utilityId must be present and non-empty
_buyer_utility_id := input.message.order["beckn:buyer"]["beckn:buyerAttributes"].utilityId

_order_violations contains "buyer utilityId is missing or empty" if {
	not _buyer_utility_id
}

_order_violations contains "buyer utilityId is missing or empty" if {
	_buyer_utility_id == ""
}

# Rule 9d – Provider utilityId must be present and non-empty per order item
_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	not provider.utilityId

	msg := sprintf(
		"order item [%d]: provider utilityId is missing",
		[i],
	)
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	provider.utilityId == ""

	msg := sprintf(
		"order item [%d]: provider utilityId is empty",
		[i],
	)
}

# ===== Domain-specific @type and @context validation (EnergyTrade) =====
#
# Dual rules at known JSON locations for EnergyTrade extension types:
#   (1) Object at a known path must have the expected @type.
#   (2) Object with that @type must have the EnergyTrade @context URL.
#
# Order locations:
#   beckn:buyer.beckn:buyerAttributes                              → EnergyCustomer
#   beckn:orderAttributes                                          → EnergyTradeOrder
#   beckn:orderItems[*].beckn:orderItemAttributes.providerAttributes → EnergyCustomer
#   beckn:orderItems[*].beckn:acceptedOffer.beckn:offerAttributes   → EnergyTradeOffer
#
# Catalog locations (in _publish_violations):
#   beckn:items[*].beckn:provider.beckn:providerAttributes          → EnergyCustomer
#   beckn:items[*].beckn:itemAttributes                             → EnergyResource
#   beckn:offers[*].beckn:offerAttributes                           → EnergyTradeOffer

_energytrade_context := "https://raw.githubusercontent.com/beckn/DEG/tags/deg-1.0.0/specification/schema/EnergyTrade/v0.3/context.jsonld"

# --- Order domain: beckn:buyerAttributes → EnergyCustomer ---

_order_violations contains msg if {
	obj := input.message.order["beckn:buyer"]["beckn:buyerAttributes"]
	msg := _wrong_type("buyer beckn:buyerAttributes", obj, "EnergyCustomer")
}

_order_violations contains msg if {
	obj := input.message.order["beckn:buyer"]["beckn:buyerAttributes"]
	msg := _missing_type("buyer beckn:buyerAttributes", obj, "EnergyCustomer")
}

_order_violations contains msg if {
	obj := input.message.order["beckn:buyer"]["beckn:buyerAttributes"]
	msg := _wrong_context("buyer beckn:buyerAttributes", obj, "EnergyCustomer", _energytrade_context)
}

_order_violations contains msg if {
	obj := input.message.order["beckn:buyer"]["beckn:buyerAttributes"]
	msg := _missing_context("buyer beckn:buyerAttributes", obj, "EnergyCustomer", _energytrade_context)
}

# --- Order domain: beckn:orderAttributes → EnergyTradeOrder ---

_order_violations contains msg if { msg := _wrong_type("message.order.beckn:orderAttributes", input.message.order["beckn:orderAttributes"], "EnergyTradeOrder") }

_order_violations contains msg if { msg := _missing_type("message.order.beckn:orderAttributes", input.message.order["beckn:orderAttributes"], "EnergyTradeOrder") }

_order_violations contains msg if { msg := _wrong_context("message.order.beckn:orderAttributes", input.message.order["beckn:orderAttributes"], "EnergyTradeOrder", _energytrade_context) }

_order_violations contains msg if { msg := _missing_context("message.order.beckn:orderAttributes", input.message.order["beckn:orderAttributes"], "EnergyTradeOrder", _energytrade_context) }

# --- Order domain: providerAttributes → EnergyCustomer ---

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:orderItemAttributes"].providerAttributes
	msg := _wrong_type(sprintf("order item [%d] providerAttributes", [i]), obj, "EnergyCustomer")
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:orderItemAttributes"].providerAttributes
	msg := _missing_type(sprintf("order item [%d] providerAttributes", [i]), obj, "EnergyCustomer")
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:orderItemAttributes"].providerAttributes
	msg := _wrong_context(sprintf("order item [%d] providerAttributes", [i]), obj, "EnergyCustomer", _energytrade_context)
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:orderItemAttributes"].providerAttributes
	msg := _missing_context(sprintf("order item [%d] providerAttributes", [i]), obj, "EnergyCustomer", _energytrade_context)
}

# --- Order domain: beckn:offerAttributes → EnergyTradeOffer ---

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]["beckn:offerAttributes"]
	msg := _wrong_type(sprintf("order item [%d] beckn:offerAttributes", [i]), obj, "EnergyTradeOffer")
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]["beckn:offerAttributes"]
	msg := _missing_type(sprintf("order item [%d] beckn:offerAttributes", [i]), obj, "EnergyTradeOffer")
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]["beckn:offerAttributes"]
	msg := _wrong_context(sprintf("order item [%d] beckn:offerAttributes", [i]), obj, "EnergyTradeOffer", _energytrade_context)
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]["beckn:offerAttributes"]
	msg := _missing_context(sprintf("order item [%d] beckn:offerAttributes", [i]), obj, "EnergyTradeOffer", _energytrade_context)
}

# ===== Core @type and @context dual enforcement =====
#
# Dual rules at known JSON locations:
#   (1) Object at a known path must have the expected @type.
#   (2) Object with a core beckn @type must have the core @context URL.
#
# Order locations (gated via _order_violations):
#   message.order                                        → beckn:Order
#   message.order.beckn:buyer                            → beckn:Buyer
#   message.order.beckn:fulfillment                      → beckn:Fulfillment
#   message.order.beckn:orderItems[*].beckn:acceptedOffer → beckn:Offer
#
# Catalog locations (gated via _publish_violations):
#   message.catalogs[*]                    → beckn:Catalog
#   message.catalogs[*].beckn:items[*]     → beckn:Item
#   message.catalogs[*].beckn:offers[*]    → beckn:Offer

core_context_url := "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/core/v2/context.jsonld"

# --- Helper functions (return a violation string, or are undefined) ---

_wrong_type(path, obj, expected) := sprintf(
	"%s: @type is %q; must be %q",
	[path, obj["@type"], expected],
) if {
	obj["@type"]
	obj["@type"] != expected
}

_missing_type(path, obj, expected) := sprintf(
	"%s: @type is missing; must be %q",
	[path, expected],
) if {
	is_object(obj)
	not obj["@type"]
}

_wrong_context(path, obj, expected_type, ctx_url) := sprintf(
	"%s: %s @context is %q; must be %q",
	[path, expected_type, obj["@context"], ctx_url],
) if {
	obj["@type"] == expected_type
	obj["@context"]
	obj["@context"] != ctx_url
}

_missing_context(path, obj, expected_type, ctx_url) := sprintf(
	"%s: %s @context is missing; must be %q",
	[path, expected_type, ctx_url],
) if {
	obj["@type"] == expected_type
	not obj["@context"]
}

# --- Order location: message.order → beckn:Order ---

_order_violations contains msg if { msg := _wrong_type("message.order", input.message.order, "beckn:Order") }

_order_violations contains msg if { msg := _missing_type("message.order", input.message.order, "beckn:Order") }

_order_violations contains msg if { msg := _wrong_context("message.order", input.message.order, "beckn:Order", core_context_url) }

_order_violations contains msg if { msg := _missing_context("message.order", input.message.order, "beckn:Order", core_context_url) }

# --- Order location: message.order.beckn:buyer → beckn:Buyer ---

_order_violations contains msg if { msg := _wrong_type("message.order.beckn:buyer", input.message.order["beckn:buyer"], "beckn:Buyer") }

_order_violations contains msg if { msg := _missing_type("message.order.beckn:buyer", input.message.order["beckn:buyer"], "beckn:Buyer") }

_order_violations contains msg if { msg := _wrong_context("message.order.beckn:buyer", input.message.order["beckn:buyer"], "beckn:Buyer", core_context_url) }

_order_violations contains msg if { msg := _missing_context("message.order.beckn:buyer", input.message.order["beckn:buyer"], "beckn:Buyer", core_context_url) }

# --- Order location: message.order.beckn:fulfillment → beckn:Fulfillment ---

_order_violations contains msg if { msg := _wrong_type("message.order.beckn:fulfillment", input.message.order["beckn:fulfillment"], "beckn:Fulfillment") }

_order_violations contains msg if { msg := _missing_type("message.order.beckn:fulfillment", input.message.order["beckn:fulfillment"], "beckn:Fulfillment") }

_order_violations contains msg if { msg := _wrong_context("message.order.beckn:fulfillment", input.message.order["beckn:fulfillment"], "beckn:Fulfillment", core_context_url) }

_order_violations contains msg if { msg := _missing_context("message.order.beckn:fulfillment", input.message.order["beckn:fulfillment"], "beckn:Fulfillment", core_context_url) }

# --- Order location: beckn:orderItems[*].beckn:acceptedOffer → beckn:Offer ---

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]
	msg := _wrong_type(sprintf("order item [%d] beckn:acceptedOffer", [i]), obj, "beckn:Offer")
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]
	msg := _missing_type(sprintf("order item [%d] beckn:acceptedOffer", [i]), obj, "beckn:Offer")
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]
	msg := _wrong_context(sprintf("order item [%d] beckn:acceptedOffer", [i]), obj, "beckn:Offer", core_context_url)
}

_order_violations contains msg if {
	item := input.message.order["beckn:orderItems"][i]
	obj := item["beckn:acceptedOffer"]
	msg := _missing_context(sprintf("order item [%d] beckn:acceptedOffer", [i]), obj, "beckn:Offer", core_context_url)
}

# ===== Action-gated violations (public API) =====
#
# Rules are gated by message structure, not by action name, so they
# automatically apply to all beckn actions (confirm, on_confirm, select,
# on_select, init, on_init, status, on_status, update, on_update,
# catalog_publish) without false positives.

# Common rules (domain, version): apply to ALL actions
violations contains msg if {
	some msg in _common_violations
}

# Order validation rules: apply when message.order exists (skip bare status requests)
violations contains msg if {
	input.message.order
	input.context.action != "status"
	some msg in _order_violations
}

# Catalog publish action: network-based catalog item validation
violations contains msg if {
	input.context.action == "catalog_publish"
	some msg in _publish_violations
}

# Test ID consistency: apply when order items exist (skip bare status requests)
violations contains msg if {
	input.message.order
	input.context.action != "status"
	some msg in _test_consistency_violations
}

# ===== Catalog publish rules =====
#
# For catalog_publish messages, items are at message.catalogs[].beckn:items[].
# Each beckn:Item has beckn:networkId (array) and beckn:provider.beckn:providerAttributes.
# - Production network: providerAttributes must exist with an approved DISCOM.
# - Non-production network: provider must use test identifiers.

_production_network_id := "p2p-interdiscom-trading-pilot-network"

# Approved DISCOMs for production network (extend this list as needed)
_allowed_utility_ids := {"TPDDL", "PVVNL", "BRPL"}

# Helper: extract provider attributes from a catalog item
_catalog_provider(item) := item["beckn:provider"]["beckn:providerAttributes"]

# Publish Rule 1 — Production: beckn:providerAttributes must exist
_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	_production_network_id in item["beckn:networkId"]
	not item["beckn:provider"]["beckn:providerAttributes"]

	msg := sprintf(
		"catalog item [%d]: beckn:providerAttributes is missing on production network item",
		[i],
	)
}

# Publish Rule 2 — Production: provider utilityId must be an approved DISCOM
_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	_production_network_id in item["beckn:networkId"]
	provider := _catalog_provider(item)
	not provider.utilityId in _allowed_utility_ids

	msg := sprintf(
		"catalog item [%d]: provider utilityId %q is not an approved DISCOM; must be one of %v",
		[i, provider.utilityId, _allowed_utility_ids],
	)
}

# Publish Rule 3 — Non-production: provider meterId must be TEST_METER_SELLER
_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	net_id := item["beckn:networkId"][_]
	net_id != _production_network_id
	provider := _catalog_provider(item)
	provider.meterId
	provider.meterId != "TEST_METER_SELLER"

	msg := sprintf(
		"catalog item [%d]: non-production network %q: provider meterId is %q; must be TEST_METER_SELLER",
		[i, net_id, provider.meterId],
	)
}

# Publish Rule 4 — Non-production: provider utilityId must be TEST_DISCOM_SELLER
_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	net_id := item["beckn:networkId"][_]
	net_id != _production_network_id
	provider := _catalog_provider(item)
	provider.utilityId
	provider.utilityId != "TEST_DISCOM_SELLER"

	msg := sprintf(
		"catalog item [%d]: non-production network %q: provider utilityId is %q; must be TEST_DISCOM_SELLER",
		[i, net_id, provider.utilityId],
	)
}

# Publish Rule 5 — Validity-to-delivery gap (mirrors O2)
_publish_violations contains msg if {
	offer := input.message.catalogs[_]["beckn:offers"][j]
	offer_attrs := offer["beckn:offerAttributes"]

	dw := _delivery_window(offer_attrs)
	dw != null
	vw := _validity_window(offer_attrs)
	vw != null

	delivery_start := time.parse_rfc3339_ns(dw["schema:startTime"])
	validity_end_str := vw["schema:endTime"]
	validity_end := time.parse_rfc3339_ns(validity_end_str)

	gap_hours := (delivery_start - validity_end) / ns_per_hour
	gap_hours < min_lead_hours

	msg := sprintf(
		"catalog offer [%d]: validity window end (%s) is only %v hours before delivery start; minimum gap is %v hours",
		[j, validity_end_str, gap_hours, min_lead_hours],
	)
}

# Publish Rule 5b — Delivery window must be exactly 1 hour (mirrors O3)
_publish_violations contains msg if {
	offer := input.message.catalogs[_]["beckn:offers"][j]
	offer_attrs := offer["beckn:offerAttributes"]

	dw := _delivery_window(offer_attrs)
	dw != null

	start_str := dw["schema:startTime"]
	end_str := dw["schema:endTime"]
	duration_hours := (time.parse_rfc3339_ns(end_str) - time.parse_rfc3339_ns(start_str)) / ns_per_hour

	duration_hours != 1

	msg := sprintf(
		"catalog offer [%d]: delivery window (%s to %s) is %v hours; must be exactly 1 hour",
		[j, start_str, end_str, duration_hours],
	)
}

# Publish Rule 6 — Currency must be INR (mirrors O6)
_publish_violations contains msg if {
	offer := input.message.catalogs[_]["beckn:offers"][j]
	currency := offer["beckn:price"]["schema:priceCurrency"]
	currency != "INR"

	msg := sprintf(
		"catalog offer [%d]: schema:priceCurrency is %q; must be INR",
		[j, currency],
	)
}

# Publish Rule 7 — Quantity unit must be kWh (mirrors O7)
_publish_violations contains msg if {
	offer := input.message.catalogs[_]["beckn:offers"][j]
	unit := offer["beckn:price"].applicableQuantity.unitText
	unit != "kWh"

	msg := sprintf(
		"catalog offer [%d]: applicableQuantity.unitText is %q; must be kWh",
		[j, unit],
	)
}

# Publish Rule 8a — Provider utilityCustomerId must be present (mirrors O8)
_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	provider := _catalog_provider(item)
	not provider.utilityCustomerId

	msg := sprintf(
		"catalog item [%d]: provider utilityCustomerId is missing",
		[i],
	)
}

_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	provider := _catalog_provider(item)
	provider.utilityCustomerId == ""

	msg := sprintf(
		"catalog item [%d]: provider utilityCustomerId is empty",
		[i],
	)
}

# Publish Rule 8b — Provider utilityId must be present (mirrors O8)
_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	provider := _catalog_provider(item)
	not provider.utilityId

	msg := sprintf(
		"catalog item [%d]: provider utilityId is missing",
		[i],
	)
}

_publish_violations contains msg if {
	item := input.message.catalogs[_]["beckn:items"][i]
	provider := _catalog_provider(item)
	provider.utilityId == ""

	msg := sprintf(
		"catalog item [%d]: provider utilityId is empty",
		[i],
	)
}

# --- Catalog domain: providerAttributes → EnergyCustomer ---

_publish_violations contains msg if {
	item := input.message.catalogs[c]["beckn:items"][i]
	obj := _catalog_provider(item)
	msg := _wrong_type(sprintf("catalog [%d] item [%d] providerAttributes", [c, i]), obj, "EnergyCustomer")
}

_publish_violations contains msg if {
	item := input.message.catalogs[c]["beckn:items"][i]
	obj := _catalog_provider(item)
	msg := _missing_type(sprintf("catalog [%d] item [%d] providerAttributes", [c, i]), obj, "EnergyCustomer")
}

_publish_violations contains msg if {
	item := input.message.catalogs[c]["beckn:items"][i]
	obj := _catalog_provider(item)
	msg := _wrong_context(sprintf("catalog [%d] item [%d] providerAttributes", [c, i]), obj, "EnergyCustomer", _energytrade_context)
}

_publish_violations contains msg if {
	item := input.message.catalogs[c]["beckn:items"][i]
	obj := _catalog_provider(item)
	msg := _missing_context(sprintf("catalog [%d] item [%d] providerAttributes", [c, i]), obj, "EnergyCustomer", _energytrade_context)
}

# --- Catalog domain: beckn:itemAttributes → EnergyResource ---

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]["beckn:itemAttributes"]
	msg := _wrong_type(sprintf("catalog [%d] item [%d] beckn:itemAttributes", [c, i]), obj, "EnergyResource")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]["beckn:itemAttributes"]
	msg := _missing_type(sprintf("catalog [%d] item [%d] beckn:itemAttributes", [c, i]), obj, "EnergyResource")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]["beckn:itemAttributes"]
	msg := _wrong_context(sprintf("catalog [%d] item [%d] beckn:itemAttributes", [c, i]), obj, "EnergyResource", _energytrade_context)
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]["beckn:itemAttributes"]
	msg := _missing_context(sprintf("catalog [%d] item [%d] beckn:itemAttributes", [c, i]), obj, "EnergyResource", _energytrade_context)
}

# --- Catalog domain: beckn:offerAttributes → EnergyTradeOffer ---

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]["beckn:offerAttributes"]
	msg := _wrong_type(sprintf("catalog [%d] offer [%d] beckn:offerAttributes", [c, o]), obj, "EnergyTradeOffer")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]["beckn:offerAttributes"]
	msg := _missing_type(sprintf("catalog [%d] offer [%d] beckn:offerAttributes", [c, o]), obj, "EnergyTradeOffer")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]["beckn:offerAttributes"]
	msg := _wrong_context(sprintf("catalog [%d] offer [%d] beckn:offerAttributes", [c, o]), obj, "EnergyTradeOffer", _energytrade_context)
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]["beckn:offerAttributes"]
	msg := _missing_context(sprintf("catalog [%d] offer [%d] beckn:offerAttributes", [c, o]), obj, "EnergyTradeOffer", _energytrade_context)
}

# --- Catalog location: message.catalogs[*] → beckn:Catalog ---

_publish_violations contains msg if {
	obj := input.message.catalogs[c]
	msg := _wrong_type(sprintf("catalog [%d]", [c]), obj, "beckn:Catalog")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]
	msg := _missing_type(sprintf("catalog [%d]", [c]), obj, "beckn:Catalog")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]
	msg := _wrong_context(sprintf("catalog [%d]", [c]), obj, "beckn:Catalog", core_context_url)
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]
	msg := _missing_context(sprintf("catalog [%d]", [c]), obj, "beckn:Catalog", core_context_url)
}

# --- Catalog location: beckn:items[*] → beckn:Item ---

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]
	msg := _wrong_type(sprintf("catalog [%d] item [%d]", [c, i]), obj, "beckn:Item")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]
	msg := _missing_type(sprintf("catalog [%d] item [%d]", [c, i]), obj, "beckn:Item")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]
	msg := _wrong_context(sprintf("catalog [%d] item [%d]", [c, i]), obj, "beckn:Item", core_context_url)
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:items"][i]
	msg := _missing_context(sprintf("catalog [%d] item [%d]", [c, i]), obj, "beckn:Item", core_context_url)
}

# --- Catalog location: beckn:offers[*] → beckn:Offer ---

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]
	msg := _wrong_type(sprintf("catalog [%d] offer [%d]", [c, o]), obj, "beckn:Offer")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]
	msg := _missing_type(sprintf("catalog [%d] offer [%d]", [c, o]), obj, "beckn:Offer")
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]
	msg := _wrong_context(sprintf("catalog [%d] offer [%d]", [c, o]), obj, "beckn:Offer", core_context_url)
}

_publish_violations contains msg if {
	obj := input.message.catalogs[c]["beckn:offers"][o]
	msg := _missing_context(sprintf("catalog [%d] offer [%d]", [c, o]), obj, "beckn:Offer", core_context_url)
}

# ===== Test ID consistency (non-publish actions) =====
#
# If ANY party (buyer OR any provider) uses a test identifier (meterId or
# utilityId starting with "TEST_"), ALL parties must use test identifiers:
#   - buyer meterId    = TEST_METER_BUYER
#   - buyer utilityId  = TEST_DISCOM_BUYER
#   - every provider meterId   must start with "TEST_"
#   - every provider utilityId must start with "TEST_"

_any_party_is_test if { startswith(_buyer_meter_id, "TEST_") }

_any_party_is_test if { startswith(_buyer_utility_id, "TEST_") }

_any_party_is_test if {
	item := input.message.order["beckn:orderItems"][_]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	startswith(provider.meterId, "TEST_")
}

_any_party_is_test if {
	item := input.message.order["beckn:orderItems"][_]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	startswith(provider.utilityId, "TEST_")
}

# T1 – buyer meterId must be TEST_METER_BUYER
_test_consistency_violations contains msg if {
	_any_party_is_test
	buyer_mid := _buyer_meter_id
	buyer_mid != "TEST_METER_BUYER"

	msg := sprintf(
		"test consistency: a party uses test identifiers but buyer meterId is %q; must be TEST_METER_BUYER",
		[buyer_mid],
	)
}

# T1 – buyer utilityId must be TEST_DISCOM_BUYER
_test_consistency_violations contains msg if {
	_any_party_is_test
	buyer_uid := _buyer_utility_id
	buyer_uid != "TEST_DISCOM_BUYER"

	msg := sprintf(
		"test consistency: a party uses test identifiers but buyer utilityId is %q; must be TEST_DISCOM_BUYER",
		[buyer_uid],
	)
}

# T1 – each provider meterId must start with TEST_
_test_consistency_violations contains msg if {
	_any_party_is_test
	item := input.message.order["beckn:orderItems"][i]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	not startswith(provider.meterId, "TEST_")

	msg := sprintf(
		"test consistency: a party uses test identifiers but order item [%d] provider meterId is %q; must start with TEST_",
		[i, provider.meterId],
	)
}

# T1 – each provider utilityId must start with TEST_
_test_consistency_violations contains msg if {
	_any_party_is_test
	item := input.message.order["beckn:orderItems"][i]
	provider := item["beckn:orderItemAttributes"].providerAttributes
	not startswith(provider.utilityId, "TEST_")

	msg := sprintf(
		"test consistency: a party uses test identifiers but order item [%d] provider utilityId is %q; must start with TEST_",
		[i, provider.utilityId],
	)
}
