#!/usr/bin/env python3
"""EV charging CPO platform (BPP) reference app, Beckn 2.0 LTS.

Receives requests from its ONIX BPP receiver on /api/webhook/<action> and answers with
on_<action> callbacks through its ONIX BPP caller. In apps mode it also plays the local
discovery service (discover, catalog/publish), so every use case runs end to end on a
laptop without the hosted discovery service.

Business features: catalog of three CPOs, quoting (surge, offer discount, service fee,
overcharge estimate, buyer finder fee, outstanding dues), slot reservations with conflict
checks, BAP- or BPP-collected payment, a simulated meter with telemetry, fault injection
(EVSE inoperative, power cut, CMS offline), final billing with refunds or dues,
cancellation terms (context.try), CPO-initiated cancellation, support tickets, ratings,
tracking handles, catalog publishing and an operator dashboard.
"""
import copy
import datetime
import json
import math
import os
import pathlib
import re
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "common"))
import beckn  # noqa: E402

PORT = int(os.environ.get("PORT", "3002"))
BPP_CALLER = os.environ.get("ONIX_BPP_CALLER", "http://onix-bpp:8082/bpp/caller")
BPP_ID = os.environ.get("BPP_ID", "bpp.example.com")
BPP_URI = os.environ.get("BPP_URI", "http://beckn-router:9000/bpp/receiver")
PUBLIC_URL = os.environ.get("CPO_PUBLIC_URL", "http://localhost:3002")
CATALOG_FILES = os.environ.get("CATALOG_FILES", "").split(",")
SIM_KWH_PER_SEC = float(os.environ.get("SIM_KWH_PER_SEC", "0.25"))  # accelerated meter
OVERCHARGE_ESTIMATE_KWH = 0.3
CANCEL_FREE_MINUTES = 30
CANCEL_FEE_RATE = 0.10

LOCK = threading.RLock()
REC = beckn.Recorder()
CATALOGS = {}       # catalog id -> catalog
RESOURCES = {}      # resource id -> (catalog id, resource)
OFFERS = {}         # offer id -> (catalog id, offer)
CONTRACTS = {}      # transaction id -> state dict
RESERVATIONS = []   # {resourceId, start, end, txn}
DUES = {}           # buyer id -> outstanding INR
FAULTS = {}         # resource id -> fault code
TICKETS = {}        # ticket id -> ticket
PUBLISHED = []      # catalog publish results
COUNTERS = {"callbacks_sent": 0, "callbacks_nacked": 0, "requests": 0}


# ---------------------------------------------------------------- catalog
def index_catalog(cat):
    cat = copy.deepcopy(cat)
    cat["bppId"], cat["bppUri"] = BPP_ID, BPP_URI
    CATALOGS[cat["id"]] = cat
    for r in cat.get("resources", []):
        RESOURCES[r["id"]] = (cat["id"], r)
    for o in cat.get("offers", []):
        OFFERS[o["id"]] = (cat["id"], o)


def load_catalogs():
    for f in CATALOG_FILES:
        f = f.strip()
        if f and pathlib.Path(f).exists():
            for cat in json.load(open(f))["message"]["catalogs"]:
                if cat["id"] in CATALOGS:  # merge resources/offers of the same catalog
                    have = CATALOGS[cat["id"]]
                    ids = {r["id"] for r in have["resources"]}
                    have["resources"] += [r for r in cat["resources"] if r["id"] not in ids]
                    oids = {o["id"] for o in have["offers"]}
                    have["offers"] += [o for o in cat["offers"] if o["id"] not in oids]
                    index_catalog(have)
                else:
                    index_catalog(cat)
    print(f"catalog: {len(CATALOGS)} catalogs, {len(RESOURCES)} resources, {len(OFFERS)} offers", flush=True)


def provider_of(resource_id):
    cid, _ = RESOURCES[resource_id]
    p = CATALOGS[cid]["provider"]
    return {"id": p["id"], "descriptor": p["descriptor"]}


def offer_for(resource_id, offer_id=None):
    if offer_id and offer_id in OFFERS:
        return OFFERS[offer_id][1]
    for _, o in OFFERS.values():
        if resource_id in o.get("resourceIds", []):
            return o
    return None


def unit_rate(offer):
    attrs = offer["considerations"][0]["considerationAttributes"]
    return float(attrs["value"])


# ---------------------------------------------------------------- local discovery service
COND = re.compile(r"\s*@\.([\w@.]+)\s*(==|!=|>=|<=|>|<)\s*('[^']*'|-?\d+(?:\.\d+)?|true|false)\s*")


def get_path(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def eval_cond(obj, cond):
    """Evaluate a JSONPath filter condition (clauses joined by && / ||)."""
    for disj in cond.split("||"):
        ok = True
        for clause in disj.split("&&"):
            m = COND.fullmatch(clause.strip().strip("()"))
            if not m:
                raise ValueError(f"unsupported filter clause: {clause.strip()}")
            path, op, lit = m.groups()
            want = lit[1:-1] if lit.startswith("'") else (lit == "true" if lit in ("true", "false") else float(lit))
            have = get_path(obj, path)
            if have is None:
                ok = False
                break
            try:
                res = {"==": have == want, "!=": have != want, ">=": have >= want, "<=": have <= want,
                       ">": have > want, "<": have < want}[op]
            except TypeError:
                res = False
            if not res:
                ok = False
                break
        if ok:
            return True
    return False


def haversine_m(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def point_in_polygon(pt, ring):
    x, y, inside = pt[0], pt[1], False
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def spatial_match(points, s):
    op, geom = s["op"].upper(), s.get("geometry") or {}
    for p in points:
        if op == "S_DWITHIN" and geom.get("type") == "Point":
            if haversine_m(p, geom["coordinates"]) <= float(s.get("distanceMeters", 0)):
                return True
        elif op == "S_WITHIN" and geom.get("type") == "Polygon":
            if point_in_polygon(p, geom["coordinates"][0]):
                return True
        # S_WITHIN against a Point never matches (a charger is not "within" a point),
        # which is how PostGIS behaves; distanceMeters only applies to S_DWITHIN.
    return False


GEO_TARGETS = {
    # the two geometry paths the fabric discovery service (beckn-discovr) indexes
    "$.catalogs[*].provider.availableAt[*].geo": "provider",
    "$.catalogs[*].resources[*].resourceAttributes.chargingStation.serviceLocation.geo": "station",
}


def discover(intent):
    """Local discovery service with the semantics of the fabric discovery service:
    RFC 9535 filters on the catalogs / resources / offers arrays, S_DWITHIN in metres,
    spatial targets limited to the indexed geometry paths (anything else matches nothing)."""
    out = []
    flt = (intent.get("filters") or {}).get("expression")
    level = cond = None
    if flt:
        m = re.fullmatch(r"\$\.catalogs(\[\*\]\.resources|\[\*\]\.offers)?\[\?\((.*)\)\]", flt.strip())
        if not m:
            raise ValueError(f"unsupported filter expression {flt!r}: use an RFC 9535 filter on "
                             "$.catalogs, $.catalogs[*].resources or $.catalogs[*].offers")
        level, cond = m.group(1), m.group(2)
    for cat in CATALOGS.values():
        res, offers = list(cat["resources"]), list(cat["offers"])
        if level == "[*].resources":
            res = [r for r in res if eval_cond(r, cond)]
        elif level == "[*].offers":
            offers = [o for o in offers if eval_cond(o, cond)]
            keep = {rid for o in offers for rid in o.get("resourceIds", [])}
            res = [r for r in res if r["id"] in keep]
        elif cond is not None and not eval_cond(cat, cond):
            res = []
        for s in intent.get("spatial") or []:
            tgt = s.get("targets")
            tgt = tgt[0] if isinstance(tgt, list) else tgt
            kind = GEO_TARGETS.get(tgt)
            if kind == "provider":
                pts = [l["geo"]["coordinates"] for l in cat["provider"].get("availableAt", [])]
                if not spatial_match(pts, s):
                    res = []
            elif kind == "station":
                res = [r for r in res if spatial_match(
                    [get_path(r, "resourceAttributes.chargingStation.serviceLocation.geo.coordinates")], s)
                    if get_path(r, "resourceAttributes.chargingStation.serviceLocation.geo.coordinates")]
            else:
                res = []  # not an indexed geometry path
        text = (intent.get("textSearch") or "").lower().strip()
        if text:
            def hit(o):
                return any(text in json.dumps(o.get(k, "")).lower() for k in ("descriptor", "id", "resourceAttributes"))
            res = [r for r in res if hit(r) or hit(cat["provider"]) or text in json.dumps(cat["descriptor"]).lower()]
        if not res:
            continue
        ids = {r["id"] for r in res}
        offers = [o for o in offers if ids & set(o.get("resourceIds", []))]
        c = copy.deepcopy(cat)
        c["resources"], c["offers"] = res, offers
        out.append(c)
    return out


# ---------------------------------------------------------------- pricing
def quote_components(rate, kwh, buyer_id, delivered=None):
    """Quote at select/init (delivered None) or final bill at stop (delivered kWh)."""
    billed = kwh if delivered is None else min(delivered, kwh)
    base = rate * billed
    comps = [
        ("UNIT", base, f"Charging energy ({rate:g} INR/kWh x {billed:g} kWh)"),
        ("SURCHARGE", base * 0.20, "Surge price (20% of energy cost)"),
        ("DISCOUNT", -base * 0.15, "Offer discount (15% of energy cost)"),
        ("FEE", 10.0, "Service fee"),
    ]
    if delivered is None:
        comps.append(("FEE", rate * OVERCHARGE_ESTIMATE_KWH,
                      f"Overcharge estimate ({OVERCHARGE_ESTIMATE_KWH:g} kWh, refunded if unused)"))
    elif delivered > kwh:
        extra = round(delivered - kwh, 3)
        comps.append(("FEE", rate * extra,
                      f"Overcharge: {extra:g} kWh delivered after the charger lost its CMS link"))
    comps.append(("FEE", base * 0.025, "Buyer finder fee (2.5% of energy cost)"))
    due = DUES.get(buyer_id, 0)
    if delivered is None and due > 0:
        comps.append(("FEE", due, "Outstanding balance from an earlier session"))
    return [(t, round(v, 2), d) for t, v, d in comps]


def total(comps):
    return round(sum(v for _, v, _ in comps), 2)


# ---------------------------------------------------------------- contract rendering
def participant_cpo(st):
    p = provider_of(st["resourceId"])
    return {"id": p["id"], "descriptor": p["descriptor"]}


def render(st, contract_status=None):
    rid = st["resourceId"]
    offer = OFFERS[st["offerId"]][1]
    c = {}
    if st.get("id"):
        c["id"] = st["id"]
    if st.get("descriptor"):
        c["descriptor"] = st["descriptor"]
    c["status"] = {"code": contract_status or st["contractStatus"]}
    c["participants"] = [participant_cpo(st)] + ([st["buyer"]] if st.get("buyer") else [])
    c["commitments"] = [{
        "id": "commitment-001",
        "status": {"descriptor": {"code": st["commitmentStatus"]}},
        "resources": [{"id": rid, "quantity": {"unitText": "Kilowatt Hour", "unitCode": "KWH",
                                               "unitQuantity": st["kwh"]}}],
        "offer": {"id": offer["id"], "descriptor": offer.get("descriptor"), "provider": offer.get("provider"),
                  "resourceIds": offer["resourceIds"], "considerations": offer.get("considerations")},
    }]
    if st.get("components"):
        c["consideration"] = [{"id": "consideration-001", "status": {"code": st["considerationStatus"]},
                               "considerationAttributes": beckn.price_spec("INR", total(st["components"]),
                                                                          st["components"])}]
    if st.get("session"):
        s = st["session"]
        c["performance"] = [{
            "id": "fulfillment-001", "status": {"code": s["sessionStatus"]}, "commitmentIds": ["commitment-001"],
            "performanceAttributes": beckn.session_attrs(
                sessionStatus=s["sessionStatus"], connectorStatus=s.get("connectorStatus"),
                connectorType=RESOURCES[rid][1]["resourceAttributes"].get("connectorType"),
                maxPowerKW=RESOURCES[rid][1]["resourceAttributes"].get("maxPowerKW"),
                meteredEnergyKWh=s.get("energy"), meteredDurationMinutes=s.get("minutes"),
                chargingTelemetry=s.get("telemetry"), totalCost=s.get("totalCost"),
                lastUpdated=s.get("lastUpdated"), reservationId=st.get("reservationId")),
        }]
    if st.get("settlements"):
        c["settlements"] = st["settlements"]
    if st.get("preferences"):
        c["contractAttributes"] = beckn.session_attrs(buyerFinderFee={"feeType": "PERCENTAGE", "feeValue": 2.5},
                                                      preferences=st["preferences"])
    return c


def send(action, st, message, error=None, try_=None):
    ctx = {"version": beckn.VERSION, "action": action, "networkId": beckn.NETWORK_ID,
           "bapId": st["bapId"], "bapUri": st["bapUri"], "bppId": BPP_ID, "bppUri": BPP_URI,
           "transactionId": st["txn"], "messageId": st.get("replyTo") or beckn.new_id(),
           "timestamp": beckn.now_iso(), "ttl": "PT30S"}
    if try_ is not None:
        ctx["try"] = try_
    body = {"context": ctx, "message": message}
    if error:
        body["error"] = error
    t0 = time.time()
    code, resp = beckn.post_json(f"{BPP_CALLER}/{action}", body)
    ok = code == 200 and (resp.get("message") or {}).get("status") == "ACK"
    with LOCK:
        COUNTERS["callbacks_sent"] += 1
        COUNTERS["callbacks_nacked"] += 0 if ok else 1
    REC.add("out", action, body, "ACK" if ok else f"NACK {code} {json.dumps(resp)[:200]}", int((time.time() - t0) * 1000))
    if not ok:
        print(f"{action} NACK {code}: {json.dumps(resp)[:300]}", flush=True)
    return ok


def biz_error(code, message, path, cause=None):
    e = {"code": code, "message": message, "details": {"path": path}}
    if cause:
        e["details"]["cause"] = cause
    return e


# ---------------------------------------------------------------- meter
def meter(st):
    s = st.get("session")
    if not s or s["sessionStatus"] != "ACTIVE":
        return
    elapsed = time.time() - s["startedAt"]
    target = st["kwh"] + (0.6 if st.get("cmsOffline") else 0)
    s["energy"] = round(min(target, elapsed * SIM_KWH_PER_SEC), 3)
    s["minutes"] = round(elapsed * 60 * SIM_KWH_PER_SEC / 0.83, 1)  # ~50 kW equivalent
    soc = round(40 + 60 * s["energy"] / max(st["kwh"], 0.1) * 0.4, 1)
    s["telemetry"] = (s.get("telemetry") or [])[-4:] + [{
        "eventTime": beckn.now_iso(),
        "metrics": [{"name": "STATE_OF_CHARGE", "value": soc, "unitCode": "PERCENTAGE"},
                    {"name": "POWER", "value": 48.5, "unitCode": "KW"},
                    {"name": "ENERGY", "value": s["energy"], "unitCode": "KWH"},
                    {"name": "VOLTAGE", "value": 392, "unitCode": "VLT"},
                    {"name": "CURRENT", "value": 123.7, "unitCode": "AMP"}]}]
    s["lastUpdated"] = beckn.now_iso()


def close_session(st, status, delivered=None):
    """Stop metering, compute the final bill and the refund (or the amount still owed)."""
    meter(st)
    s = st["session"]
    energy = round(delivered if delivered is not None else st.get("deliverOverride") or s.get("energy") or 0, 3)
    s.update(sessionStatus=status, energy=energy, connectorStatus="AVAILABLE", lastUpdated=beckn.now_iso())
    final = quote_components(st["rate"], st["kwh"], st["buyerId"], delivered=energy)
    paid = st.get("paidAmount", 0.0)
    bill = total(final)
    s["totalCost"] = {"inclVat": bill}
    st.update(components=final, considerationStatus="FINAL")
    diff = round(paid - bill, 2)
    if diff > 0:
        st["settlements"].append({"id": f"settlement-{len(st['settlements']) + 1:03d}",
                                  "considerationId": "consideration-001", "status": "COMPLETE",
                                  "settlementAttributes": beckn.payment_attrs(
                                      "REFUNDED", diff, "BUYER", id=f"refund-{st['txn'][:8]}",
                                      txnRef=f"RFND-{st['txn'][:8]}", paidAt=beckn.now_iso())})
    elif diff < 0:
        DUES[st["buyerId"]] = round(DUES.get(st["buyerId"], 0) - diff, 2)
        st["settlements"].append({"id": f"settlement-{len(st['settlements']) + 1:03d}",
                                  "considerationId": "consideration-001", "status": "DRAFT",
                                  "settlementAttributes": beckn.payment_attrs("PENDING", -diff, "BPP")})
    st.update(contractStatus="COMPLETE", commitmentStatus="CLOSED")
    for r in RESERVATIONS:
        if r["txn"] == st["txn"]:
            r["released"] = True
    return diff


# ---------------------------------------------------------------- request handlers
def state_for(ctx):
    with LOCK:
        st = CONTRACTS.setdefault(ctx["transactionId"], {"txn": ctx["transactionId"]})
    st.update(bapId=ctx["bapId"], bapUri=ctx["bapUri"], replyTo=ctx["messageId"])
    return st


def h_discover(ctx, msg):
    try:
        cats = discover(msg.get("intent") or {})
        err = None
    except ValueError as e:
        cats, err = [], biz_error("BIZ_GENERIC_ERROR", str(e), "$.message.intent.filters.expression")
    st = {"txn": ctx["transactionId"], "bapId": ctx["bapId"], "bapUri": ctx["bapUri"], "replyTo": ctx["messageId"]}
    send("on_discover", st, {"catalogs": cats}, error=err)


def h_select(ctx, msg):
    st = state_for(ctx)
    c = msg["contract"]
    cm = c["commitments"][0]
    rid, oid = cm["resources"][0]["id"], cm["offer"]["id"]
    if rid not in RESOURCES:
        return send("on_select", st, {"contract": c},
                    error=biz_error("BIZ_ITEM_NOT_FOUND", f"No charger {rid}", "$.message.contract.commitments[0]"))
    buyer = next((p for p in c.get("participants", []) if (p.get("participantAttributes") or {}).get("@type") == "Consumer"), None)
    prefs = ((c.get("contractAttributes") or {}).get("preferences")) or {}
    offer = offer_for(rid, oid)
    st.update(resourceId=rid, offerId=offer["id"], kwh=float(cm["resources"][0]["quantity"]["unitQuantity"]),
              buyer=buyer, buyerId=(buyer or {}).get("id", "anonymous"), preferences=prefs,
              rate=unit_rate(offer), contractStatus="DRAFT", commitmentStatus="DRAFT",
              considerationStatus="QUOTED", settlements=[])
    if prefs.get("startTime") and prefs.get("endTime"):
        a, b = beckn.parse_iso(prefs["startTime"]), beckn.parse_iso(prefs["endTime"])
        clash = [r for r in RESERVATIONS if r["resourceId"] == rid and not r.get("released")
                 and r["txn"] != st["txn"] and a < r["end"] and r["start"] < b]
        if clash:
            st.pop("components", None)
            return send("on_select", st, {"contract": render(st)}, error=biz_error(
                "BIZ_FULFILLMENT_UNAVAILABLE",
                f"Requested slot {prefs['startTime']} - {prefs['endTime']} overlaps an existing booking.",
                "$.message.contract.contractAttributes.preferences"))
    st["components"] = quote_components(st["rate"], st["kwh"], st["buyerId"])
    send("on_select", st, {"contract": render(st)})


def h_init(ctx, msg):
    st = state_for(ctx)
    c = msg["contract"]
    buyer = next((p for p in c.get("participants", []) if (p.get("participantAttributes") or {}).get("@type") == "Consumer"), None)
    if buyer:
        st["buyer"] = buyer
    req = (c.get("settlements") or [{}])[0].get("settlementAttributes") or {}
    mode = req.get("beckn:beneficiary", "BPP")
    st.setdefault("id", f"order-ev-{st['txn'][:8]}")
    st["paymentMode"] = mode
    amount = total(st["components"])
    extra = {"id": f"payment-{st['txn'][:8]}", "acceptedPaymentMethod": ["UPI", "CREDIT_CARD", "WALLET"]}
    if mode == "BPP":
        extra.update(paymentURL=f"{PUBLIC_URL}/pay/{st['txn']}", txnRef=f"TXN-{st['txn'][:8]}")
    else:  # BAP collects and settles with the CPO; the CPO shares its settlement account
        extra["paymentAttributes"] = {
            "@context": "https://raw.githubusercontent.com/beckn/protocol-specifications-v2/tags/core-2.0.0-rc-eos-release/schema/PaymentSettlement/v1/context.jsonld",
            "@type": "PaymentSettlement",
            "settlementAccounts": [{"beneficiaryId": BPP_ID, "accountHolderName": provider_of(st["resourceId"])["descriptor"]["name"],
                                    "accountNumber": "1234567890123", "ifscCode": "HDFC0001234",
                                    "bankName": "HDFC Bank", "vpa": "cpo@upi"}]}
    st["settlements"] = [{"id": "settlement-001", "considerationId": "consideration-001", "status": "DRAFT",
                          "settlementAttributes": beckn.payment_attrs("INITIATED", amount, mode, **extra)}]
    send("on_init", st, {"contract": render(st)})


def mark_paid(st, txn_ref):
    a = st["settlements"][0]["settlementAttributes"]
    a.update({"beckn:paymentStatus": "COMPLETED", "beckn:txnRef": txn_ref, "beckn:paidAt": beckn.now_iso()})
    st["settlements"][0]["status"] = "COMPLETE"
    st["paidAmount"] = a["beckn:amount"]["value"]
    if DUES.get(st["buyerId"]) and any("Outstanding" in d for _, _, d in st["components"]):
        DUES.pop(st["buyerId"], None)  # dues were collected with this payment


def h_confirm(ctx, msg):
    st = state_for(ctx)
    c = msg["contract"]
    if st.get("paymentMode") == "BAP":
        a = ((c.get("settlements") or [{}])[0].get("settlementAttributes") or {})
        if a.get("beckn:paymentStatus") == "COMPLETED":
            mark_paid(st, a.get("beckn:txnRef") or f"BAP-{st['txn'][:8]}")
    if st.get("paidAmount") is None:
        return send("on_confirm", st, {"contract": render(st)}, error=biz_error(
            "BIZ_PAYMENT_FAILED", "Payment not received for this order.", "$.message.contract.settlements[0]"))
    prefs = st.get("preferences") or {}
    start = beckn.parse_iso(prefs["startTime"]) if prefs.get("startTime") else datetime.datetime.now(datetime.timezone.utc)
    end = beckn.parse_iso(prefs["endTime"]) if prefs.get("endTime") else start + datetime.timedelta(hours=1)
    st["reservationId"] = f"RSV-{st['txn'][:8]}"
    RESERVATIONS.append({"resourceId": st["resourceId"], "start": start, "end": end, "txn": st["txn"]})
    st.update(contractStatus="ACTIVE", commitmentStatus="ACTIVE", considerationStatus="AGREED",
              session={"sessionStatus": "PENDING", "connectorStatus": "AVAILABLE"})
    send("on_confirm", st, {"contract": render(st)})


def h_status(ctx, msg):
    st = state_for(ctx)
    if "resourceId" not in st:
        return send("on_status", {**st, "resourceId": None}, {"contract": msg["contract"]}, error=biz_error(
            "BIZ_ORDER_NOT_FOUND", "Unknown contract", "$.message.contract.id"))
    meter(st)
    if st.get("session") and st["session"]["sessionStatus"] == "PENDING":
        st["session"]["connectorStatus"] = "UNAVAILABLE" if FAULTS.get(st["resourceId"]) else "PREPARING"
    send("on_status", st, {"contract": render(st)})


def h_update(ctx, msg):
    st = state_for(ctx)
    perf = (msg["contract"].get("performance") or [{}])[0]
    want = (perf.get("performanceAttributes") or {}).get("sessionStatus")
    s = st.get("session") or {}
    if want == "ACTIVE":
        if FAULTS.get(st["resourceId"]):
            s["connectorStatus"] = "UNAVAILABLE"
            evse = RESOURCES[st["resourceId"]][1]["resourceAttributes"].get("evseId")
            return send("on_update", st, {"contract": render(st)}, error=biz_error(
                "BIZ_FULFILLMENT_UNAVAILABLE", "Charging session could not be started at the requested EVSE.",
                "$.message.contract.performance[0]",
                {"code": "EVSE_INOPERATIVE", "message": f"OCPI 2.2: StartSession rejected, EVSE {evse} status is INOPERATIVE."}))
        if s.get("sessionStatus") != "PENDING":
            return send("on_update", st, {"contract": render(st)}, error=biz_error(
                "BIZ_INVALID_STATE_TRANSITION", f"Session is {s.get('sessionStatus')}, cannot start.",
                "$.message.contract.performance[0]"))
        s.update(sessionStatus="ACTIVE", connectorStatus="UNAVAILABLE", startedAt=time.time(), energy=0.0,
                 lastUpdated=beckn.now_iso())
        return send("on_update", st, {"contract": render(st)})
    if want in ("STOP", "COMPLETED"):
        if s.get("sessionStatus") != "ACTIVE":
            return send("on_update", st, {"contract": render(st)}, error=biz_error(
                "BIZ_INVALID_STATE_TRANSITION", f"Session is {s.get('sessionStatus')}, cannot stop.",
                "$.message.contract.performance[0]"))
        close_session(st, "COMPLETED")
        send("on_update", st, {"contract": render(st)})
        beckn.later(send_invoice, st, delay=0.5)
        return
    send("on_update", st, {"contract": render(st)}, error=biz_error(
        "BIZ_INVALID_UPDATE_TARGET", f"Unsupported update: sessionStatus={want}", "$.message.contract.performance[0]"))


def send_invoice(st):
    st["descriptor"] = {"name": f"EV charging session {st['id']}", "docs": [{
        "label": f"Tax invoice INV-{st['txn'][:8].upper()}", "mimeType": "application/pdf",
        "url": f"{PUBLIC_URL}/invoices/{st['id']}.pdf"}]}
    st["replyTo"] = None
    send("on_update", st, {"contract": render(st)})


def cancellation_fee(st):
    start = (st.get("preferences") or {}).get("startTime")
    if not start:
        return 0.0
    minutes = (beckn.parse_iso(start) - datetime.datetime.now(datetime.timezone.utc)).total_seconds() / 60
    return 0.0 if minutes > CANCEL_FREE_MINUTES else round(st["rate"] * st["kwh"] * CANCEL_FEE_RATE, 2)


def h_cancel(ctx, msg):
    st = state_for(ctx)
    preview = bool(ctx.get("try"))
    if st.get("contractStatus") != "ACTIVE" or (st.get("session") or {}).get("sessionStatus") != "PENDING":
        return send("on_cancel", st, {"contract": render(st)}, error=biz_error(
            "BIZ_INVALID_STATE_TRANSITION", "Only a booked, not yet started session can be cancelled.",
            "$.message.contract.id"), try_=preview or None)
    fee = cancellation_fee(st)
    refund = round(st["paidAmount"] - fee, 2)
    terms = (f"Free cancellation up to {CANCEL_FREE_MINUTES} minutes before the slot; "
             f"{int(CANCEL_FEE_RATE * 100)}% of the energy cost after that.")
    if preview:
        view = copy.deepcopy(st)
        view["descriptor"] = {"code": "CANCELLATION_TERMS", "shortDesc": terms}
        view["components"] = [("FEE", fee, "Cancellation fee")] if fee else [("FEE", 0.0, "No cancellation fee")]
        view["considerationStatus"] = "QUOTED"
        view["settlements"] = st["settlements"] + [{"id": "settlement-002", "considerationId": "consideration-001",
                                                   "status": "DRAFT", "settlementAttributes": beckn.payment_attrs(
                                                       "PENDING", refund, "BUYER")}]
        view.pop("session", None)
        return send("on_cancel", view, {"contract": render(view)}, try_=True)
    reason = (msg["contract"].get("descriptor") or {}).get("code", "USER_CANCELLED")
    do_cancel(st, reason, "Cancelled by the consumer.", fee)
    send("on_cancel", st, {"contract": render(st)})


def do_cancel(st, code, text, fee):
    refund = round(st["paidAmount"] - fee, 2)
    st.update(contractStatus="CANCELLED", commitmentStatus="CLOSED", considerationStatus="REFUNDED",
              descriptor={"code": code, "shortDesc": text})
    if fee:
        st["components"] = [("FEE", fee, "Cancellation fee")]
        st["considerationStatus"] = "FINAL"
    st["settlements"].append({"id": f"settlement-{len(st['settlements']) + 1:03d}", "considerationId": "consideration-001",
                              "status": "COMPLETE", "settlementAttributes": beckn.payment_attrs(
                                  "REFUNDED", refund, "BUYER", id=f"refund-{st['txn'][:8]}",
                                  txnRef=f"RFND-{st['txn'][:8]}", paidAt=beckn.now_iso())})
    st.pop("session", None)
    for r in RESERVATIONS:
        if r["txn"] == st["txn"]:
            r["released"] = True


def h_rate(ctx, msg):
    st = state_for(ctx)
    ratings = msg.get("ratingInputs", [])
    st.setdefault("ratings", []).extend(ratings)
    send("on_rate", st, {"ratings": ratings})


def h_support(ctx, msg):
    st = state_for(ctx)
    sup = msg["support"]
    tid = f"SUP-{len(TICKETS) + 1:05d}"
    TICKETS[tid] = {"id": tid, "orderId": sup.get("orderId"), "txn": st["txn"], "status": "OPEN",
                    "descriptor": sup.get("descriptor"), "opened": beckn.now_iso()}
    send("on_support", st, {"support": support_reply(tid)})


def support_reply(tid):
    t = TICKETS[tid]
    return {"orderId": t["orderId"],
            "descriptor": {"code": t["status"], "name": f"Ticket {tid} {t['status'].lower()}",
                           "shortDesc": t.get("resolution") or (t.get("descriptor") or {}).get("shortDesc") or "We are on it."},
            "channels": [beckn.pack("support", "SupportInfo", {
                "name": "CPO Support Desk", "telephone": "18001080", "email": "support@cpo.example.com",
                "url": f"{PUBLIC_URL}/support/{tid}", "hoursAvailable": "Mon-Sun 24/7 IST",
                "channels": ["PHONE", "EMAIL", "WEB", "CHAT"],
                **({"callbackStatus": "COMPLETED"} if t["status"] == "RESOLVED" else {})})]}


def h_track(ctx, msg):
    st = state_for(ctx)
    meter(st)
    s = st.get("session") or {}
    send("on_track", st, {"tracking": {
        "contract": {"id": st["id"], "commitments": render(st)["commitments"]},
        "status": "ACTIVE" if s.get("sessionStatus") == "ACTIVE" else "INACTIVE",
        "url": f"{PUBLIC_URL}/live/{st['txn']}",
        "trackingAttributes": beckn.session_attrs(sessionStatus=s.get("sessionStatus"), meteredEnergyKWh=s.get("energy"),
                                                  lastUpdated=s.get("lastUpdated") or beckn.now_iso())}})


def h_catalog_publish(ctx, msg):
    """Local discovery service: index published catalogs and acknowledge."""
    results = []
    for cat in msg.get("catalogs", []):
        index_catalog(cat)
        results.append({"catalogId": cat["id"], "status": "ACCEPTED",
                        "stats": {"itemCount": len(cat.get("resources", [])), "providerCount": 1}})
    body = {"context": {"version": beckn.VERSION, "action": "catalog/on_publish", "networkId": beckn.NETWORK_ID,
                        "bppId": BPP_ID, "bppUri": BPP_URI, "transactionId": ctx["transactionId"],
                        "messageId": ctx["messageId"], "timestamp": beckn.now_iso(), "ttl": "PT30S"},
            "message": {"results": results}}
    code, resp = beckn.post_json(f"{BPP_CALLER}/catalog/on_publish", body)
    REC.add("out", "catalog/on_publish", body, "ACK" if code == 200 else f"NACK {code}")


def h_catalog_on_publish(ctx, msg):
    PUBLISHED.append({"at": beckn.now_iso(), "results": msg.get("results")})


HANDLERS = {"discover": h_discover, "select": h_select, "init": h_init, "confirm": h_confirm, "status": h_status,
            "update": h_update, "cancel": h_cancel, "rate": h_rate, "support": h_support, "track": h_track,
            "catalog/publish": h_catalog_publish, "catalog/on_publish": h_catalog_on_publish}


# ---------------------------------------------------------------- admin (business operations)
def admin(op, body):
    txn = body.get("txn")
    st = CONTRACTS.get(txn) if txn else None
    if op == "fault":
        if body.get("clear"):
            FAULTS.pop(body["resourceId"], None)
        else:
            FAULTS[body["resourceId"]] = body.get("code", "EVSE_INOPERATIVE")
        return {"faults": FAULTS}
    if op == "deliver":
        st["deliverOverride"] = float(body["kwh"])
        return {"txn": txn, "deliverOverride": st["deliverOverride"]}
    if op == "cms-offline":
        st["cmsOffline"] = True
        st["deliverOverride"] = round(st["kwh"] + float(body.get("extraKwh", OVERCHARGE_ESTIMATE_KWH)), 3)
        return {"txn": txn, "deliverOverride": st["deliverOverride"]}
    if op == "power-cut":
        diff = close_session(st, "INTERRUPTED", delivered=float(body["kwh"]) if "kwh" in body else None)
        st["contractStatus"] = "COMPLETE"
        st["replyTo"] = None
        send("on_status", st, {"contract": render(st)})
        return {"txn": txn, "refund": diff}
    if op == "cpo-cancel":
        do_cancel(st, body.get("code", "CPO_CHARGER_FAULT"),
                  body.get("text", "The reserved charger is out of service; the booking is cancelled with a full refund."), 0.0)
        st["replyTo"] = None
        send("on_cancel", st, {"contract": render(st)})
        return {"txn": txn, "status": "CANCELLED"}
    if op == "resolve-ticket":
        t = TICKETS[body["ticketId"]]
        t.update(status="RESOLVED", resolution=body.get("text", "Resolved by the CPO."))
        tst = CONTRACTS[t["txn"]]
        tst["replyTo"] = None
        send("on_support", tst, {"support": support_reply(t["id"])})
        return t
    if op == "publish-catalog":
        cat = body["catalog"]
        pub = {"context": {"version": beckn.VERSION, "action": "catalog/publish", "networkId": beckn.NETWORK_ID,
                           "bppId": BPP_ID, "bppUri": BPP_URI, "transactionId": beckn.new_id(),
                           "messageId": beckn.new_id(), "timestamp": beckn.now_iso(), "ttl": "PT30S"},
               "message": {"catalogs": [cat]}}
        code, resp = beckn.post_json(f"{BPP_CALLER}/catalog/publish", pub)
        REC.add("out", "catalog/publish", pub, "ACK" if code == 200 else f"NACK {code} {json.dumps(resp)[:200]}")
        return {"status": code, "response": resp}
    if op == "seed-dues":
        DUES[body["buyerId"]] = float(body["amount"])
        return {"dues": DUES}
    if op == "reset":  # back to the shipped catalog and an empty book
        for d in (CONTRACTS, FAULTS, TICKETS, DUES, CATALOGS, RESOURCES, OFFERS):
            d.clear()
        RESERVATIONS.clear()
        PUBLISHED.clear()
        load_catalogs()
        return {"reset": True, "catalogs": len(CATALOGS)}
    raise ValueError(f"unknown admin op {op}")


def summary():
    with LOCK:
        sessions = [{"txn": t, "id": s.get("id"), "resource": s.get("resourceId"), "status": s.get("contractStatus"),
                     "session": (s.get("session") or {}).get("sessionStatus"), "kwh": s.get("kwh"),
                     "paid": s.get("paidAmount"), "billed": total(s["components"]) if s.get("components") else None,
                     "buyer": s.get("buyerId")} for t, s in CONTRACTS.items() if s.get("resourceId")]
        revenue = round(sum(x["billed"] or 0 for x in sessions if x["status"] == "COMPLETE"), 2)
        return {"catalogs": len(CATALOGS), "resources": len(RESOURCES), "contracts": len(sessions),
                "completed": sum(1 for x in sessions if x["status"] == "COMPLETE"),
                "cancelled": sum(1 for x in sessions if x["status"] == "CANCELLED"),
                "revenueINR": revenue, "dues": DUES, "faults": FAULTS, "tickets": list(TICKETS.values()),
                "counters": COUNTERS, "published": PUBLISHED[-5:], "sessions": sessions[-50:]}


DASHBOARD = (pathlib.Path(__file__).parent / "dashboard.html")


class Handler(beckn.JsonHandler):
    routes = {("POST", "/api/webhook"): "webhook", ("GET", "/api/health"): "health",
              ("GET", "/api/state"): "state", ("GET", "/api/messages"): "messages",
              ("POST", "/admin"): "admin", ("POST", "/pay"): "pay", ("GET", "/pay"): "pay_page",
              ("GET", "/"): "dashboard"}

    def webhook(self, action, body):
        with LOCK:
            COUNTERS["requests"] += 1
        REC.add("in", action, body)
        h = HANDLERS.get(action)
        if not h:
            return 404, {"error": f"unsupported action {action}"}, "application/json"
        beckn.later(h, body["context"], body.get("message") or {})
        return 200, beckn.ack(body["context"].get("messageId")), "application/json"

    def health(self, _, __):
        return 200, {"status": "ok", "service": "ev-cpo-app"}, "application/json"

    def state(self, _, __):
        return 200, summary(), "application/json"

    def messages(self, _, __):
        return 200, REC.dump(), "application/json"

    def admin(self, op, body):
        # No lock here: ops such as publish-catalog call back into this app's own webhook.
        return 200, admin(op, body or {}), "application/json"

    def pay(self, txn, body):
        st = CONTRACTS[txn]
        mark_paid(st, (body or {}).get("txnRef") or f"PG-{txn[:8]}")
        st["replyTo"] = None
        send("on_status", st, {"contract": render(st)})  # unsolicited: payment received
        return 200, {"paid": st["paidAmount"], "contract": st["id"]}, "application/json"

    def pay_page(self, txn, _):
        st = CONTRACTS.get(txn) or {}
        amt = st.get("components") and total(st["components"])
        html = (f"<html><body style='font-family:sans-serif'><h3>Pay INR {amt} for {st.get('id')}</h3>"
                f"<form method='post' onsubmit=\"fetch('/pay/{txn}',{{method:'POST'}}).then(()=>document.body.innerHTML='Paid');return false\">"
                f"<button>Pay with UPI (simulated)</button></form></body></html>")
        return 200, html.encode(), "text/html"

    def dashboard(self, _, __):
        return 200, DASHBOARD.read_bytes(), "text/html"


if __name__ == "__main__":
    load_catalogs()
    beckn.serve(Handler, PORT)
