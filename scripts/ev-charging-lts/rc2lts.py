#!/usr/bin/env python3
"""Convert the DEG EV charging examples from the Beckn 2.0 rc shape
(core-2.0.0-rc-eos-release: message.order, beckn:Order) to Beckn 2.0 LTS
(core-v2.0.0-lts: message.contract).

Usage: rc2lts.py <rc examples dir> <out dir> [--profile canonical|devkit]

Mapping rules (documented in examples/ev-charging/v2/README.md):
  order                  -> contract
  order.orderItems[]     -> contract.commitments[] (resource + quantity + offer)
  order.orderValue       -> contract.consideration[] (PriceSpecification v2.1)
  order.payment          -> contract.settlements[] (Payment v2.0 pack)
  order.fulfillment      -> contract.performance[] (ChargingSession, EvChargingSession v2.0)
  order.orderAttributes  -> contract.contractAttributes (ChargingSession)
  order.seller / buyer   -> contract.participants[]
  catalog (multi-CPO)    -> one Catalog per provider; station locations -> provider.availableAt
  item / offer           -> Resource (ChargingService) / Offer (ChargingOffer, price in considerations)
  discover filters       -> absolute JSONPath from the catalog root (fabric discovr convention)
  discover spatial       -> S_DWITHIN on $.catalogs[*].provider.availableAt[*].geo
"""
import copy
import json
import pathlib
import re
import sys
import uuid

PACKS = "https://schema.nfh.global"
CTX = {
    "service": f"{PACKS}/EvChargingService/v2.0/context.jsonld",
    "offer": f"{PACKS}/EvChargingOffer/v2.0/context.jsonld",
    "session": f"{PACKS}/EvChargingSession/v2.0/context.jsonld",
    "price": f"{PACKS}/PriceSpecification/v2.1/context.jsonld",
    "consumer": f"{PACKS}/Consumer/v2.0/context.jsonld",
    "payment": f"{PACKS}/Payment/v2.0/context.jsonld",
    "support": f"{PACKS}/SupportInfo/v2.1/context.jsonld",
}
NETWORK_ID = "nfh.global/testnet-evcharging"
GEO_TARGET = "$.catalogs[*].provider.availableAt[*].geo"
RESOURCES = "$.catalogs[*].resources"
OFFERS = "$.catalogs[*].offers"

# rc order status -> LTS Contract.status.code (enum DRAFT|ACTIVE|CANCELLED|COMPLETE)
CONTRACT_STATUS = {
    "CREATED": "DRAFT", "PENDING": "DRAFT", "REJECTED": "DRAFT",
    "CONFIRMED": "ACTIVE", "INPROGRESS": "ACTIVE",
    "COMPLETED": "COMPLETE", "CANCELLED": "CANCELLED",
}
# rc order status -> LTS Commitment.status.descriptor.code (enum DRAFT|ACTIVE|CLOSED)
COMMITMENT_STATUS = {
    "CREATED": "DRAFT", "PENDING": "DRAFT", "REJECTED": "DRAFT",
    "CONFIRMED": "ACTIVE", "INPROGRESS": "ACTIVE",
    "COMPLETED": "CLOSED", "CANCELLED": "CLOSED",
}
# rc payment status -> LTS Settlement.status (enum DRAFT|COMMITTED|COMPLETE)
SETTLEMENT_STATUS = {
    "INITIATED": "DRAFT", "PENDING": "DRAFT", "AUTHORIZED": "COMMITTED",
    "COMPLETED": "COMPLETE", "CAPTURED": "COMPLETE", "REFUNDED": "COMPLETE",
    "PARTIALLY_REFUNDED": "COMPLETE",
}
# consideration status code by rc order status (free-text Descriptor.code)
CONSIDERATION_STATUS = {
    "CREATED": "QUOTED", "PENDING": "QUOTED", "REJECTED": "QUOTED",
    "CONFIRMED": "AGREED", "INPROGRESS": "AGREED",
    "COMPLETED": "FINAL", "CANCELLED": "REFUNDED",
}
ACTION_RENAME = {"rating": "rate", "on_rating": "on_rate"}

DEVKIT_IDS = {
    "example-bap.com": "bap.example.com",
    "app.example.com": "bap.example.com",
    "example-bpp.com": "bpp.example.com",
    "example-cds.com": "bpp.example.com",
}

PROVIDER_NAMES = {}
OFFERS_BY_ITEM = {}
QTY_BY_ITEM = {}


def g(o, key, default=None):
    """Read an rc field that may or may not carry the beckn:/schema: prefix."""
    if not isinstance(o, dict):
        return default
    for k in (f"beckn:{key}", f"schema:{key}", key):
        if k in o:
            return o[k]
    return default


def clean(o):
    """Drop None values and empty containers, recursively."""
    if isinstance(o, dict):
        out = {k: clean(v) for k, v in o.items() if v is not None}
        return {k: v for k, v in out.items() if v not in ({}, [])}
    if isinstance(o, list):
        return [clean(v) for v in o if v is not None]
    return o


def descriptor(d):
    if not isinstance(d, dict):
        return None
    return clean({"name": g(d, "name"), "code": g(d, "code"),
                  "shortDesc": g(d, "shortDesc"), "longDesc": g(d, "longDesc")})


def pack(ctx_key, type_name, body):
    out = {"@context": CTX[ctx_key], "@type": type_name}
    out.update({k: v for k, v in body.items() if not k.startswith("@")})
    return out


def strip_ld(o):
    """Remove JSON-LD @type/@context from nested plain objects (e.g. beckn:Location
    inside chargingStation.serviceLocation), which the v2.0 packs do not declare."""
    if isinstance(o, dict):
        return {k: strip_ld(v) for k, v in o.items() if k not in ("@type", "@context")}
    if isinstance(o, list):
        return [strip_ld(v) for v in o]
    return o


# ---------------------------------------------------------------- context
def context(rc_ctx, profile, action=None):
    a = action or ACTION_RENAME.get(rc_ctx["action"], rc_ctx["action"])
    ids = (lambda x: DEVKIT_IDS.get(x, x)) if profile == "devkit" else (lambda x: x)
    c = {
        "version": "2.0.0",
        "action": a,
        "networkId": NETWORK_ID,
        "bapId": ids(rc_ctx.get("bap_id")),
        "bapUri": rc_ctx.get("bap_uri"),
        "bppId": ids(rc_ctx.get("bpp_id")),
        "bppUri": rc_ctx.get("bpp_uri"),
        "transactionId": rc_ctx.get("transaction_id"),
        "messageId": rc_ctx.get("message_id"),
        "timestamp": rc_ctx.get("timestamp"),
        "ttl": rc_ctx.get("ttl"),
    }
    if a == "discover":
        # discover goes to the discovery service, not a BPP
        c.pop("bppId"), c.pop("bppUri")
        c["schemaContext"] = [CTX["service"], CTX["offer"]]
    if profile == "devkit":
        if c.get("bapId"):
            c["bapUri"] = f"https://{c['bapId']}"
        if c.get("bppId"):
            c["bppUri"] = f"https://{c['bppId']}"
    return clean(c)


# ---------------------------------------------------------------- discover
# rc filters that name ids found in no catalog; filter on the attribute that identifies
# the thing instead (verified against the fabric discovery service, beckn-discovr).
EVSE_FILTERS = {
    "IND*CPO1*cs-01*evse-01*connectorid-01": "@.resourceAttributes.evseId == 'IN*ECO*BTM*01*CCS2*A'",
    "ev-charger-ccs2-001": "@.resourceAttributes.chargingStation.id == 'IN-ECO-BTM-STATION-01'",
}


def rewrite_expr(expr):
    """rc filters are relative to an item. LTS filters are absolute RFC 9535 JSONPath from
    the catalog root, filtering the resources / offers / catalogs arrays themselves:
    $.catalogs[*].resources[?(...)], $.catalogs[*].offers[?(...)], $.catalogs[?(...)]."""
    m = re.fullmatch(r"\$\[\?\((.*)\)\]", expr.strip())
    cond = m.group(1).strip() if m else expr
    ids = re.fullmatch(r"@\.beckn:id\s*==\s*'([^']*)'", cond)
    if ids and ids.group(1) in EVSE_FILTERS:
        return f"{RESOURCES}[?({EVSE_FILTERS[ids.group(1)]})]"
    cond = re.sub(r"@\.beckn:id\s*==\s*", "@.id == ", cond)
    if "@.beckn:provider.beckn:id" in cond:
        return "$.catalogs[?(" + cond.replace("@.beckn:provider.beckn:id", "@.provider.id") + ")]"
    # Nexon EV -> a 4-wheeler with a CCS2 inlet; LTS resources carry vehicle class and
    # connector type, not make/model.
    cond = re.sub(r"@\.beckn:fulfillment\.beckn:deliveryAttributes\.vehicle\.make == '[^']*' && "
                  r"@\.beckn:fulfillment\.beckn:deliveryAttributes\.vehicle\.model == '[^']*'\s*",
                  "@.resourceAttributes.vehicleType == '4-WHEELER' && @.resourceAttributes.connectorType == 'CCS2'", cond)
    window = re.search(r"@\.beckn:availabilityWindow\.schema:startTime <= ('[^']*') && "
                       r"@\.beckn:availabilityWindow\.schema:endTime >= ('[^']*')", cond)
    if window:
        # LTS Resource has no availability window; opening hours live on offer validity.
        return f"{OFFERS}[?(@.validity.startTime <= {window.group(1)} && @.validity.endTime >= {window.group(2)})]"
    cond = cond.replace("@.beckn:itemAttributes.", "@.resourceAttributes.")
    return f"{RESOURCES}[?({cond.strip()})]"


def intent(msg):
    out = {}
    if "filters" in msg:
        out["filters"] = {"type": msg["filters"].get("type", "jsonpath"),
                          "expression": rewrite_expr(msg["filters"]["expression"])}
    if "spatial" in msg:
        out["spatial"] = clean([{
            # distanceMeters only applies to S_DWITHIN (ignored for other ops)
            "op": "S_DWITHIN" if s["op"].lower() == "s_dwithin" else s["op"].upper(),
            "targets": GEO_TARGET,
            "geometry": s["geometry"],
            "distanceMeters": s.get("distanceMeters"),
        } for s in msg["spatial"]])
    return {"intent": out}


# ---------------------------------------------------------------- catalog
def price_consideration(cid, price, status=None):
    return clean({"id": cid, "status": {"code": status} if status else None,
                  "considerationAttributes": pack("price", "PriceSpecification", price)})


def offer_attrs(rc_offer):
    a = dict(g(rc_offer, "offerAttributes") or {})
    body = {k: v for k, v in a.items() if not k.startswith("@")}
    methods = g(rc_offer, "acceptedPaymentMethod")
    if methods:
        body["acceptedPaymentMethods"] = methods
    return pack("offer", "ChargingOffer", body) if body else None


def provider_ref(pid):
    return {"id": pid, "descriptor": {"name": PROVIDER_NAMES.get(pid) or pid}}


def resource_from_item(item):
    attrs = strip_ld(g(item, "itemAttributes") or {})
    return clean({"id": g(item, "id"), "descriptor": descriptor(g(item, "descriptor")),
                  "resourceAttributes": pack("service", "ChargingService", attrs)})


def offer_from_rc(rc_offer, items_by_id):
    oid = g(rc_offer, "id")
    resource_ids = g(rc_offer, "items") or []
    validity = g(rc_offer, "validity") or {}
    window = {}
    for rid in resource_ids:
        w = g(items_by_id.get(rid, {}), "availabilityWindow")
        if w:
            window = w[0]
            break
    period = clean({"startDate": g(validity, "startDate"), "endDate": g(validity, "endDate"),
                    "startTime": g(window, "startTime"), "endTime": g(window, "endTime")})
    pid = g(rc_offer, "provider")
    pid = g(pid, "id") if isinstance(pid, dict) else pid
    price = g(rc_offer, "price")
    return clean({
        "id": oid,
        "descriptor": descriptor(g(rc_offer, "descriptor")),
        "provider": provider_ref(pid) if pid else None,
        "resourceIds": resource_ids,
        "considerations": [price_consideration(f"price-{oid}", price)] if price else None,
        "validity": period or None,
        "offerAttributes": offer_attrs(rc_offer),
    })


def catalogs(rc_catalogs):
    out = []
    for cat in rc_catalogs:
        items = g(cat, "items") or []
        offers = g(cat, "offers") or []
        items_by_id = {g(i, "id"): i for i in items}
        by_provider = {}
        for it in items:
            pid = g(g(it, "provider") or {}, "id")
            by_provider.setdefault(pid, {"items": [], "offers": []})["items"].append(it)
        for of in offers:
            # An offer belongs to the CPO whose chargers it prices. The rc specific-EVSE
            # catalog declares EcoPower's offer under GoGreen; derive it from the items.
            owners = [g(g(items_by_id[i], "provider") or {}, "id") for i in (g(of, "items") or []) if i in items_by_id]
            pid = owners[0] if owners else g(of, "provider")
            pid = g(pid, "id") if isinstance(pid, dict) else pid
            of = dict(of)
            of["beckn:provider"] = pid
            by_provider.setdefault(pid, {"items": [], "offers": []})["offers"].append(of)
        multi = len(by_provider) > 1
        for pid, grp in by_provider.items():
            locations, seen = [], set()
            for it in grp["items"]:
                loc = ((g(it, "itemAttributes") or {}).get("chargingStation") or {}).get("serviceLocation")
                key = json.dumps(loc, sort_keys=True)
                if loc and key not in seen:
                    seen.add(key)
                    locations.append(strip_ld(loc))
            out.append(clean({
                "id": f"{g(cat, 'id')}-{pid}" if multi else g(cat, "id"),
                "descriptor": descriptor(g(cat, "descriptor")),
                "bppId": g(cat, "bppId"),
                "bppUri": g(cat, "bppUri"),
                "provider": clean({"id": pid, "descriptor": {"name": PROVIDER_NAMES.get(pid) or pid},
                                   "availableAt": locations}),
                "resources": [resource_from_item(i) for i in grp["items"]],
                "offers": [offer_from_rc(o, items_by_id) for o in grp["offers"]],
            }))
    return {"catalogs": out}


# ---------------------------------------------------------------- order -> contract
def participants(order):
    out = []
    seller = g(order, "seller")
    if seller:
        out.append(provider_ref(seller))
    buyer = g(order, "buyer")
    if isinstance(buyer, dict):
        person = clean({"id": g(buyer, "id"), "name": g(buyer, "displayName"),
                        "telephone": g(buyer, "telephone"), "email": g(buyer, "email")})
        out.append(clean({
            "id": g(buyer, "id"),
            "descriptor": {"name": g(buyer, "displayName") or g(buyer, "id")},
            "participantAttributes": pack("consumer", "Consumer",
                                          clean({"role": g(buyer, "role"), "person": person or None})),
        }))
    return out


def commitments(order, status):
    out = []
    for n, it in enumerate(g(order, "orderItems") or [], 1):
        rid = g(it, "orderedItem")
        rc_offer = g(it, "acceptedOffer") or OFFERS_BY_ITEM.get(rid)
        if rc_offer:
            oid = g(rc_offer, "id")
            pid = g(rc_offer, "provider") or g(order, "seller")
            price = g(rc_offer, "price") or g(it, "price")
            offer = clean({
                "id": oid,
                "descriptor": descriptor(g(rc_offer, "descriptor")),
                "provider": provider_ref(pid) if pid else None,
                "resourceIds": g(rc_offer, "items") or [rid],
                "considerations": [price_consideration(f"price-{oid}", price)] if price else None,
            })
        else:
            offer = {"id": f"offer-{rid}", "resourceIds": [rid]}
        out.append(clean({
            "id": f"commitment-{n:03d}",
            "status": {"descriptor": {"code": COMMITMENT_STATUS.get(status, "DRAFT")}},
            # LTS requires a quantity on every committed resource; later rc steps omit
            # it, so the quantity agreed at select is carried forward.
            "resources": [clean({"id": rid, "quantity": g(it, "quantity") or QTY_BY_ITEM.get(rid)})],
            "offer": offer,
        }))
    return out


def session_attrs(rc_attrs):
    if not isinstance(rc_attrs, dict) or rc_attrs.get("@type") not in ("ChargingSession", None):
        return None
    body = {k: v for k, v in rc_attrs.items() if not k.startswith("@")}
    return pack("session", "ChargingSession", body) if body else None


def settlement(pay):
    attrs = {"@context": CTX["payment"], "@type": "Payment"}
    for k in ("id", "paymentStatus", "amount", "paymentURL", "txnRef", "paidAt",
              "acceptedPaymentMethod", "beneficiary", "paymentAttributes"):
        v = g(pay, k)
        if v is not None:
            attrs[f"beckn:{k}"] = v
    return clean({
        "id": "settlement-001",
        "considerationId": "consideration-001",
        "status": SETTLEMENT_STATUS.get(g(pay, "paymentStatus"), "DRAFT"),
        "settlementAttributes": attrs,
    })


def contract(order):
    status = g(order, "orderStatus") or "CREATED"
    comms = commitments(order, status)
    c = {
        "id": g(order, "id"),
        "status": {"code": CONTRACT_STATUS.get(status, "DRAFT")},
        "participants": participants(order),
        "commitments": comms,
    }
    value = g(order, "orderValue")
    if value:
        c["consideration"] = [price_consideration("consideration-001", value,
                                                  CONSIDERATION_STATUS.get(status, "QUOTED"))]
    ful = g(order, "fulfillment")
    if ful:
        d = g(ful, "deliveryAttributes") or {}
        c["performance"] = [clean({
            "id": g(ful, "id"),
            "status": {"code": d.get("sessionStatus", "PENDING")},
            "commitmentIds": [x["id"] for x in comms],
            "performanceAttributes": session_attrs(d),
        })]
    pay = g(order, "payment")
    if pay:
        c["settlements"] = [settlement(pay)]
        if order.get("_refund"):
            c["settlements"].append({
                "id": "settlement-002", "considerationId": "consideration-001", "status": "COMPLETE",
                "settlementAttributes": {"@context": CTX["payment"], "@type": "Payment", "beckn:id": "refund-001",
                                         "beckn:paymentStatus": "REFUNDED",
                                         "beckn:amount": {"currency": "INR", "value": order["_refund"]},
                                         "beckn:beneficiary": "BUYER"}})
    ca = session_attrs(g(order, "orderAttributes"))
    if ca:
        c["contractAttributes"] = ca
    return {"contract": clean(c)}


# ---------------------------------------------------------------- rating / support
def rate(msg):
    out = []
    for r in msg.get("ratings", []):
        fb = r.get("feedback") or {}
        out.append(clean({
            "target": {"id": r.get("id"), "descriptor": {"code": r.get("category")}},
            "range": clean({"bestRating": r.get("bestRating"), "worstRating": r.get("worstRating"),
                            "ratingValue": r.get("ratingValue")}),
            "feedbackFormSubmission": clean({
                "data": clean({"comments": fb.get("comments"),
                               "tags": ",".join(fb.get("tags", [])) or None}),
            }) if fb else None,
        }))
    return {"ratingInputs": out}


def on_rate(msg, rated):
    form = msg.get("feedbackForm") or {}
    out = []
    for r in rated.get("ratingInputs", []):
        r = copy.deepcopy(r)
        if form.get("submission_id"):
            r.setdefault("feedbackFormSubmission", {"data": {}})
            r["feedbackFormSubmission"]["id"] = form.get("url")
        out.append(r)
    return {"ratings": out}


def support_info(s):
    return pack("support", "SupportInfo", clean({
        "name": s.get("name"), "telephone": s.get("phone"), "email": s.get("email"),
        "url": s.get("url"), "hoursAvailable": s.get("hours"), "channels": s.get("channels"),
    }))


def support(msg):
    s = msg.get("support") or {}
    # LTS: the Support object MUST carry a descriptor describing the support needed.
    return {"support": clean({
        "orderId": msg.get("refId"),
        "descriptor": {"name": "Help with charging session", "code": msg.get("refType") or "ORDER"},
        "channels": [support_info(s)],
    })}


def on_support(msg, order_id):
    s = msg.get("support") or {}
    return {"support": clean({"orderId": order_id,
                              "descriptor": {"name": "Support ticket SUP-20250730-001", "code": "OPEN"},
                              "channels": [support_info(s)]})}


# ---------------------------------------------------------------- data fixes
FLOW_ITEM = "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
SELLER_ALIASES = {"cpo1.com": "ecopower-charging"}  # rc switches seller id mid-flow
UNIT_FIXES = {"POWER": "KW", "ENERGY": "KWH"}       # rc swaps these two units


RATE, KWH, EST_KWH = 45.0, 2.5, 0.3


def priced(kwh, delivered=None):
    """The pricing model shared with the reference CPO app: energy, 20% surge, 15% offer
    discount, 10 INR service fee, an overcharge estimate on quotes (refunded if unused),
    2.5% buyer finder fee. Lines are rounded, and the total is the sum of the lines."""
    billed = kwh if delivered is None else min(delivered, kwh)
    base = RATE * billed
    lines = [("UNIT", base, f"Charging energy ({RATE:g} INR/kWh x {billed:g} kWh)"),
             ("SURCHARGE", base * 0.20, "Surge price (20% of energy cost)"),
             ("DISCOUNT", -base * 0.15, "Offer discount (15% of energy cost)"),
             ("FEE", 10.0, "Service fee")]
    if delivered is None:
        lines.append(("FEE", RATE * EST_KWH, f"Overcharge estimate ({EST_KWH:g} kWh, refunded if unused)"))
    lines.append(("FEE", base * 0.025, "Buyer finder fee (2.5% of energy cost)"))
    comps = [{"type": t, "value": round(v, 2), "currency": "INR", "description": d} for t, v, d in lines]
    return {"currency": "INR", "value": round(sum(c["value"] for c in comps), 2), "components": comps}


QUOTE = priced(KWH)              # 144.43
FINAL = priced(KWH, KWH)         # 130.93 for the full 2.5 kWh
RC_QUOTE = 143.95                # the rc quote, whose lines did not match their labels


def normalize(rc):
    """Correct inconsistencies in the rc examples so the LTS set is one coherent flow."""
    for cat in rc.get("message", {}).get("catalogs", []) or []:
        for it in cat.get("beckn:items", []):
            a = it.get("beckn:itemAttributes") or {}
            # GoGreen's connector B carries EcoPower's connector A EVSE id in the rc data
            if it.get("beckn:id", "").endswith("*CCS2-B") and a.get("evseId") == "IN*ECO*BTM*01*CCS2*A":
                a["evseId"] = "IN*ECO*BTM*01*CCS2*B"
    order = rc.get("message", {}).get("order")
    if isinstance(order, dict):
        if order.get("beckn:seller") in SELLER_ALIASES:
            order["beckn:seller"] = SELLER_ALIASES[order["beckn:seller"]]
        for it in order.get("beckn:orderItems", []):
            if it.get("beckn:orderedItem") == "pe-charging-01":  # truncated id in 20_on_cancel
                it["beckn:orderedItem"] = FLOW_ITEM
        if (order.get("beckn:orderValue") or {}).get("value") == RC_QUOTE:
            order["beckn:orderValue"] = copy.deepcopy(QUOTE)
        pay = order.get("beckn:payment") or {}
        if (pay.get("beckn:amount") or {}).get("value") == RC_QUOTE:
            pay["beckn:amount"]["value"] = QUOTE["value"]
        ful = order.get("beckn:fulfillment") or {}
        attrs = ful.get("beckn:deliveryAttributes") or {}
        if order.get("beckn:orderStatus") == "COMPLETED" and attrs.get("sessionStatus") == "COMPLETED":
            # the final bill: 2.5 kWh delivered, the unused overcharge estimate refunded
            order["beckn:orderValue"] = copy.deepcopy(FINAL)
            attrs.update(meteredEnergyKWh=KWH, totalCost={"inclVat": FINAL["value"]})
            order["_refund"] = round(QUOTE["value"] - FINAL["value"], 2)
        for ev in attrs.get("chargingTelemetry", []):
            for m in ev.get("metrics", []):
                if m.get("name") in UNIT_FIXES:
                    m["unitCode"] = UNIT_FIXES[m["name"]]
    return rc


# ---------------------------------------------------------------- driver
def convert(rc, profile, state):
    rc = normalize(copy.deepcopy(rc))
    ctx = rc["context"]
    msg = rc["message"]
    action = ctx["action"]
    if action == "discover":
        m = intent(msg)
    elif action == "on_discover":
        m = catalogs(msg["catalogs"])
        if state.get("file") == "ev-charging-specific-evse-catalog.json":
            # answer to the by-EVSE discover: only the scanned connector's catalog
            m["catalogs"] = [c for c in m["catalogs"]
                             if any(r["resourceAttributes"].get("evseId") == "IN*ECO*BTM*01*CCS2*A" for r in c["resources"])]
    elif action == "rating":
        m = rate(msg)
        state["rated"] = m
    elif action == "on_rating":
        m = on_rate(msg, state.get("rated", {"ratingInputs": []}))
    elif action == "support":
        m = support(msg)
        state["order_id"] = msg.get("refId")
    elif action == "on_support":
        m = on_support(msg, state.get("order_id"))
    else:
        m = contract(msg["order"])
    out = {"context": context(ctx, profile), "message": m}
    if action == "discover":
        out["context"]["messageId"] = str(uuid.uuid5(uuid.NAMESPACE_URL, "deg-ev-lts/discover/" + state["file"]))
    if profile == "devkit":
        out = json.loads(json.dumps(out).replace("example-bap.com", "bap.example.com")
                         .replace("example-bpp.com", "bpp.example.com"))
    return out


def prescan(src):
    for f in sorted(src.rglob("*.json")):
        d = json.load(open(f))
        msg = d.get("message", {})
        for cat in msg.get("catalogs", []) or []:
            for it in g(cat, "items") or []:
                prov = g(it, "provider") or {}
                PROVIDER_NAMES[g(prov, "id")] = g(g(prov, "descriptor") or {}, "name")
        for it in g(msg.get("order", {}), "orderItems") or []:
            if g(it, "acceptedOffer"):
                OFFERS_BY_ITEM.setdefault(g(it, "orderedItem"), g(it, "acceptedOffer"))
            if g(it, "quantity"):
                QTY_BY_ITEM.setdefault(g(it, "orderedItem"), g(it, "quantity"))


def main():
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    profile = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--profile" else "canonical"
    prescan(src)
    state = {}
    for f in sorted(src.rglob("*.json")):
        state["file"] = f.name
        out = convert(json.load(open(f)), profile, state)
        target = dst / f.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
        print(f"{f.relative_to(src)} -> {out['context']['action']}: {', '.join(out['message'])}")


if __name__ == "__main__":
    main()
