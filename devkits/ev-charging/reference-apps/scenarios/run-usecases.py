#!/usr/bin/env python3
"""Run every EV charging use case as real Beckn 2.0 LTS transactions and report metrics.

Drives the consumer app (BAP) API; uses the CPO app's operations API for business events
(faults, power cut, CPO cancellation, ticket resolution, catalog publishing). Every
request and callback goes through both ONIX adapters (signed, registry-checked,
schema-validated). Expected values are computed here, independently of the apps.

Usage:
  python3 run-usecases.py [--iterations N] [--bap http://localhost:3001] [--cpo http://localhost:3002]
                          [--catalog <LTS on_discover file>] [--out <dir>] [--only UC-01,UC-05]
Exit code 0 only if every transaction passes.
"""
import argparse
import datetime
import json
import math
import pathlib
import statistics
import sys
import time
import traceback
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--iterations", type=int, default=1)
ap.add_argument("--bap", default="http://localhost:3001")
ap.add_argument("--cpo", default="http://localhost:3002")
ap.add_argument("--catalog", default=",".join(str(HERE.parent.parent / "uc1-ev-charging/examples/02_on_discover" / f)
                                              for f in ("ev-charging-discovery-catalog.json", "ev-charging-specific-evse-catalog.json")))
ap.add_argument("--discover-examples", default=str(HERE.parent.parent / "uc1-ev-charging/examples/01_discover"))
ap.add_argument("--out", default=str(HERE / "results"))
ap.add_argument("--only", default="")
args = ap.parse_args()

RATE, EST_KWH = 45.0, 0.3
BUYERS = {n: {"id": f"user-{n}", "name": n.title(), "phone": "+91-90000000%02d" % i, "email": f"{n}@example.com"}
          for i, n in enumerate(["ravi", "asha", "kiran", "meera", "dev", "lata", "arun", "nila"], 1)}


def call(base, path, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data, {"Content-Type": "application/json"} if data else {})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read() or b"{}")
    except urllib.error.HTTPError as e:
        return {"httpError": e.code, "body": e.read().decode()[:400]}


def bap(op, body):
    return call(args.bap, f"/api/{op}", body)


def cpo(op, body):
    return call(args.cpo, f"/admin/{op}", body)


class Fail(Exception):
    pass


CURRENT = []  # transactions created by the use case being run


class Txn:
    """One Beckn transaction: its steps, latencies and assertions."""

    def __init__(self, uc, name):
        self.uc, self.name, self.id, self.steps, self.t0 = uc, name, None, [], time.time()
        self.ok, self.reason = True, ""
        CURRENT.append(self)

    def step(self, action, r, expect_ok=True):
        self.id = self.id or r.get("txn") or (r.get("context") or {}).get("transactionId")
        self.steps.append({"action": action, "ok": r.get("ok"), "ms": r.get("latencyMs"),
                           "error": (r.get("error") or {}).get("code") if isinstance(r.get("error"), dict) else r.get("error")})
        if expect_ok and not r.get("ok"):
            raise Fail(f"{action} failed: {json.dumps(r.get('error') or r)[:300]}")
        if not expect_ok and r.get("ok"):
            raise Fail(f"{action} should have failed")
        return r

    def check(self, cond, what):
        if not cond:
            raise Fail(what)


# ---------------------------------------------------------------- expectations
def money(contract):
    return contract["consideration"][0]["considerationAttributes"]


def lines_total(*amounts):
    """A bill adds up its displayed (rounded) lines."""
    return round(sum(round(a, 2) for a in amounts), 2)


def quote_total(kwh, dues=0.0, rate=RATE):
    base = rate * kwh
    return lines_total(base, base * 0.2, -base * 0.15, 10, rate * EST_KWH, base * 0.025, dues)


def bill_total(kwh_booked, delivered, rate=RATE):
    billed = min(delivered, kwh_booked)
    base = rate * billed
    over = rate * (delivered - kwh_booked) if delivered > kwh_booked else 0
    return lines_total(base, base * 0.2, -base * 0.15, 10, over, base * 0.025)


def refunds(contract):
    return round(sum(s["settlementAttributes"]["beckn:amount"]["value"] for s in contract.get("settlements", [])
                     if s["settlementAttributes"].get("beckn:paymentStatus") == "REFUNDED"), 2)


def iso(minutes_from_now):
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes_from_now)).strftime("%Y-%m-%dT%H:%M:%SZ")


CATALOGS = []
for _f in args.catalog.split(","):
    for _c in json.load(open(_f))["message"]["catalogs"]:
        _have = next((x for x in CATALOGS if x["id"] == _c["id"]), None)
        if _have:  # same CPO in both files: merge, as the CPO app does
            _have["resources"] += [r for r in _c["resources"] if r["id"] not in {x["id"] for x in _have["resources"]}]
            _have["offers"] += [o for o in _c.get("offers", []) if o["id"] not in {x["id"] for x in _have["offers"]}]
        else:
            CATALOGS.append(_c)


def rate_of(resource_id):
    for c in CATALOGS:
        for o in c.get("offers", []):
            if resource_id in o["resourceIds"]:
                return float(o["considerations"][0]["considerationAttributes"]["value"])
    return RATE


def hav(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def expected_resources(pred_catalog=lambda c: True, pred_resource=lambda r, c: True):
    return sorted(r["id"] for c in CATALOGS if pred_catalog(c) for r in c["resources"] if pred_resource(r, c))


def within(c, pt, m):
    return any(hav(l["geo"]["coordinates"], pt) <= m for l in c["provider"].get("availableAt", []))


def found(r):
    return sorted(x["id"] for c in (r.get("message") or {}).get("catalogs", []) for x in c["resources"])


# ---------------------------------------------------------------- building blocks
def discover_one(t, resource_id):
    r = t.step("discover", bap("discover", {"intent": {"filters": {"type": "jsonpath",
        "expression": f"$.catalogs[*].resources[?(@.id == '{resource_id}')]"}}}))
    t.check(found(r) == [resource_id], f"QR discovery returned {found(r)}")
    return r["message"]["catalogs"][0]


def book(t, buyer, resource_id, kwh=2.5, payment="BPP", start_in=None, length=60, dues=0.0):
    """discover -> select -> init -> pay -> confirm. Returns (txn, paid, contract)."""
    cat = discover_one(t, resource_id)
    sel = {"catalog": cat, "resourceId": resource_id, "kwh": kwh, "buyer": buyer}
    if start_in is not None:
        sel.update(startTime=iso(start_in), endTime=iso(start_in + length))
    r = t.step("select", bap("select", sel))
    txn = r["txn"]
    t.id = txn
    q = money(r["message"]["contract"])
    exp = quote_total(kwh, dues, rate_of(resource_id))
    t.check(q["value"] == exp, f"quote {q['value']} != expected {exp}")
    t.check(round(sum(c["value"] for c in q["components"]), 2) == q["value"], "quote components do not add up")
    r = t.step("init", bap("init", {"txn": txn, "payment": payment}))
    pay = r["message"]["contract"]["settlements"][0]["settlementAttributes"]
    t.check(pay["beckn:beneficiary"] == payment, f"payment collector {pay['beckn:beneficiary']} != {payment}")
    if payment == "BPP":
        url = pay["beckn:paymentURL"]
        t.check(url.endswith(txn), "payment link is not for this transaction")
        call(args.cpo, f"/pay/{txn}", {})            # the driver pays on the CPO's payment page
        r = t.step("on_status (payment)", bap("wait", {"txn": txn, "action": "on_status"}))
        t.check(r["message"]["contract"]["settlements"][0]["settlementAttributes"]["beckn:paymentStatus"] == "COMPLETED",
                "payment not reported COMPLETED")
    else:
        t.step("pay (in app)", bap("pay", {"txn": txn}))
    r = t.step("confirm", bap("confirm", {"txn": txn}))
    c = r["message"]["contract"]
    t.check(c["status"]["code"] == "ACTIVE", f"contract {c['status']['code']} after confirm")
    t.check(c["performance"][0]["performanceAttributes"]["sessionStatus"] == "PENDING", "session not PENDING after confirm")
    return txn, quote_total(kwh, dues, rate_of(resource_id)), c


def charge(t, txn, kwh_booked, deliver, expect_refund=True):
    r = t.step("update (start)", bap("start", {"txn": txn}))
    t.check(r["message"]["contract"]["performance"][0]["status"]["code"] == "ACTIVE", "session not ACTIVE after start")
    time.sleep(1.2)
    r = t.step("status (live)", bap("status", {"txn": txn}))
    pa = r["message"]["contract"]["performance"][0]["performanceAttributes"]
    t.check(pa.get("meteredEnergyKWh", 0) > 0 and pa.get("chargingTelemetry"), "no live energy/telemetry while charging")
    cpo("deliver", {"txn": txn, "kwh": deliver})
    r = t.step("update (stop)", bap("stop", {"txn": txn}))
    c = r["message"]["contract"]
    t.check(c["status"]["code"] == "COMPLETE", "contract not COMPLETE after stop")
    t.check(money(c)["value"] == bill_total(kwh_booked, deliver), f"bill {money(c)['value']} != {bill_total(kwh_booked, deliver)}")
    inv = t.step("on_update (invoice)", bap("wait", {"txn": txn, "action": "on_update"}))
    t.check(inv["message"]["contract"]["descriptor"]["docs"][0]["mimeType"] == "application/pdf", "no invoice document")
    return c


# ---------------------------------------------------------------- use cases
ECO = "IND*ecopower-charging*cs-01*IN*ECO*BTM*01*CCS2*A*CCS2-A"
UCS = {}


def uc(code, title):
    def deco(fn):
        UCS[code] = (title, fn)
        return fn
    return deco


def resources_any():
    return [r["id"] for c in CATALOGS for r in c["resources"]]


@uc("UC-01", "Walk-in: scan QR, pay by UPI link, charge, live telemetry, track, stop, invoice, rate, support")
def uc01(it):
    t = Txn("UC-01", "walk-in")
    txn, paid, _ = book(t, BUYERS["ravi"], ECO, payment="BPP")
    r = t.step("status (connector)", bap("status", {"txn": txn}))
    t.check(r["message"]["contract"]["performance"][0]["performanceAttributes"].get("connectorStatus") == "PREPARING",
            "connector not PREPARING before start")
    r = t.step("update (start)", bap("start", {"txn": txn}))
    time.sleep(1.2)
    r = t.step("track", bap("track", {"txn": txn}))
    t.check(r["message"]["tracking"]["status"] == "ACTIVE" and r["message"]["tracking"]["url"], "no live tracking handle")
    cpo("deliver", {"txn": txn, "kwh": 2.5})
    r = t.step("update (stop)", bap("stop", {"txn": txn}))
    c = r["message"]["contract"]
    t.check(refunds(c) == round(paid - bill_total(2.5, 2.5), 2), f"refund {refunds(c)} != unused overcharge estimate")
    t.step("on_update (invoice)", bap("wait", {"txn": txn, "action": "on_update"}))
    r = t.step("rate", bap("rate", {"txn": txn, "value": 5, "comments": "Quick and easy"}))
    t.check(r["message"]["ratings"][0]["range"]["ratingValue"] == 5, "rating not echoed")
    r = t.step("support", bap("support", {"txn": txn, "code": "GENERAL", "name": "Receipt question", "text": "GST invoice needed"}))
    t.check(r["message"]["support"]["descriptor"]["code"] == "OPEN", "support ticket not opened")
    return [t]


@uc("UC-02", "Reservation: area + connector search, BAP-collected payment, slot, charge, invoice")
def uc02(it):
    t = Txn("UC-02", "reservation")
    pt = [77.59, 12.94]
    r = t.step("discover", bap("discover", {"intent": {
        "filters": {"type": "jsonpath", "expression": "$.catalogs[*].resources[?(@.resourceAttributes.connectorType == 'CCS2' && @.resourceAttributes.maxPowerKW >= 50)]"},
        "spatial": [{"op": "S_DWITHIN", "targets": "$.catalogs[*].provider.availableAt[*].geo",
                     "geometry": {"type": "Point", "coordinates": pt}, "distanceMeters": 10000}]}}))
    exp = expected_resources(lambda c: within(c, pt, 10000), lambda r, c: r["resourceAttributes"]["connectorType"] == "CCS2"
                             and r["resourceAttributes"]["maxPowerKW"] >= 50)
    t.check(found(r) == exp, f"area search returned {found(r)}, expected {exp}")
    txn, paid, _ = book(t, BUYERS["asha"], ECO, payment="BAP", start_in=120 + it * 200)
    charge(t, txn, 2.5, 2.5)
    return [t]


@uc("UC-03", "Discovery catalogue: every example intent, text search, S_WITHIN-with-point (must be empty)")
def uc03(it):
    out = []
    pt_btm = [77.59, 12.94]
    cases = []
    for f in sorted(pathlib.Path(args.discover_examples).glob("*.json")):
        cases.append((f.stem, json.load(open(f))["message"]["intent"]))
    cases += [("text search 'Koramangala'", {"textSearch": "Koramangala"}),
              ("S_WITHIN with a point (migration-kit style)", {"spatial": [{"op": "S_WITHIN", "targets": "$.catalogs[*].provider.availableAt[*].geo",
                                                                            "geometry": {"type": "Point", "coordinates": pt_btm}, "distanceMeters": 10000}]}),
              ("S_DWITHIN 1 km", {"spatial": [{"op": "S_DWITHIN", "targets": "$.catalogs[*].provider.availableAt[*].geo",
                                                 "geometry": {"type": "Point", "coordinates": pt_btm}, "distanceMeters": 1000}]}),
              ("S_DWITHIN 4 km on the station path", {"spatial": [{"op": "S_DWITHIN", "geometry": {"type": "Point", "coordinates": pt_btm},
                  "targets": "$.catalogs[*].resources[*].resourceAttributes.chargingStation.serviceLocation.geo", "distanceMeters": 4000}]}),
              ("migration-kit target path (not indexed: empty)", {"spatial": [{"op": "S_DWITHIN", "geometry": {"type": "Point", "coordinates": pt_btm},
                  "targets": "$['resourceAttributes']['chargingStation']['serviceLocation']['geo']", "distanceMeters": 10000}]})]
    for name, intent in cases:
        t = Txn("UC-03", name)
        try:
            r = t.step("discover", bap("discover", {"intent": intent}))
            got, exp = found(r), expect_for(intent)
            t.check(got == exp, f"{name}: got {got}, expected {exp}")
        except Fail as e:
            t.ok, t.reason = False, str(e)
        out.append(t)
    return out


def dig(o, dotted):
    for p in dotted.split("."):
        o = o.get(p) if isinstance(o, dict) else None
    return o


def clauses_hold(obj, cond):
    import re
    for path, op, lit in re.findall(r"@\.([\w.@]+) (==|>=|<=) ('[^']*'|[\d.]+)", cond):
        want = lit[1:-1] if lit.startswith("'") else float(lit)
        have = dig(obj, path)
        if have is None or (op == "==" and have != want) or (op == ">=" and not have >= want) or (op == "<=" and not have <= want):
            return False
    return True


def expect_for(intent):
    """Independent evaluation of the intents used in the examples."""
    f = (intent.get("filters") or {}).get("expression", "")

    def ok_res(r, c):
        if f.startswith("$.catalogs[?(") and not clauses_hold(c, f):
            return False
        if f.startswith("$.catalogs[*].resources[?(") and not clauses_hold(r, f):
            return False
        if f.startswith("$.catalogs[*].offers[?(") and not any(
                r["id"] in o["resourceIds"] and clauses_hold(o, f) for o in c["offers"]):
            return False
        txt = (intent.get("textSearch") or "").lower()
        if txt and txt not in json.dumps([r.get("descriptor"), r["id"], c["provider"], c.get("descriptor")]).lower():
            return False
        return True

    def ok_cat(c):
        for s in intent.get("spatial") or []:
            if s["op"].upper() != "S_DWITHIN":
                return False  # a station is never "within" a point
            if s["targets"] not in ("$.catalogs[*].provider.availableAt[*].geo",
                                    "$.catalogs[*].resources[*].resourceAttributes.chargingStation.serviceLocation.geo"):
                return False  # not an indexed geometry path
            if not within(c, s["geometry"]["coordinates"], s["distanceMeters"]):
                return False
        return True
    return expected_resources(ok_cat, ok_res)


@uc("UC-04", "Slot conflict: a second driver asks for an overlapping slot and is refused")
def uc04(it):
    a = Txn("UC-04", "first booking")
    book(a, BUYERS["kiran"], ECO, start_in=600 + it * 200, length=60)
    b = Txn("UC-04", "overlapping request")
    cat = discover_one(b, ECO)
    r = b.step("select (overlap)", bap("select", {"catalog": cat, "resourceId": ECO, "kwh": 2.5, "buyer": BUYERS["meera"],
                                                  "startTime": iso(630 + it * 200), "endTime": iso(690 + it * 200)}), expect_ok=False)
    b.check(r["error"]["code"] == "BIZ_FULFILLMENT_UNAVAILABLE", f"wrong error {r['error']}")
    return [a, b]


@uc("UC-05", "Outstanding dues: an overcharge beyond the estimate becomes dues, collected on the next booking")
def uc05(it):
    t1 = Txn("UC-05", "session with large overcharge")
    buyer = BUYERS["dev"]
    txn, paid, _ = book(t1, buyer, ECO)
    t1.step("update (start)", bap("start", {"txn": txn}))
    cpo("cms-offline", {"txn": txn, "extraKwh": 0.8})
    r = t1.step("update (stop)", bap("stop", {"txn": txn}))
    c = r["message"]["contract"]
    owed = round(bill_total(2.5, 3.3) - paid, 2)
    t1.check(owed > 0, "overcharge did not exceed the estimate")
    t1.check(any(s["settlementAttributes"]["beckn:paymentStatus"] == "PENDING" and s["settlementAttributes"]["beckn:amount"]["value"] == owed
                 for s in c["settlements"]), f"no pending settlement for {owed}")
    t1.step("on_update (invoice)", bap("wait", {"txn": txn, "action": "on_update"}))
    t2 = Txn("UC-05", "next booking carries the dues")
    book(t2, buyer, ECO, dues=owed)
    return [t1, t2]


@uc("UC-06", "Start rejected: EVSE inoperative (error chain), fault cleared, retry succeeds")
def uc06(it):
    t = Txn("UC-06", "start rejected then retried")
    txn, paid, _ = book(t, BUYERS["lata"], ECO)
    cpo("fault", {"resourceId": ECO})
    try:
        r = t.step("update (start, EVSE down)", bap("start", {"txn": txn}), expect_ok=False)
        t.check(r["error"]["details"]["cause"]["code"] == "EVSE_INOPERATIVE", "missing EVSE_INOPERATIVE cause")
    finally:
        cpo("fault", {"resourceId": ECO, "clear": True})
    charge(t, txn, 2.5, 2.5)
    return [t]


@uc("UC-07", "Power cut mid-session: CPO reports INTERRUPTED, bills energy delivered, refunds the rest")
def uc07(it):
    t = Txn("UC-07", "power cut")
    txn, paid, _ = book(t, BUYERS["arun"], ECO)
    t.step("update (start)", bap("start", {"txn": txn}))
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    cpo("power-cut", {"txn": txn, "kwh": 1.2})
    r = t.step("on_status (interrupted, unsolicited)", bap("wait", {"txn": txn, "action": "on_status", "after": since}))
    c = r["message"]["contract"]
    t.check(c["performance"][0]["performanceAttributes"]["sessionStatus"] == "INTERRUPTED", "session not INTERRUPTED")
    t.check(refunds(c) == round(paid - bill_total(2.5, 1.2), 2), f"refund {refunds(c)} != {round(paid - bill_total(2.5, 1.2), 2)}")
    return [t]


@uc("UC-08", "CMS offline overcharge within the estimate: overcharge billed, nothing refunded")
def uc08(it):
    t = Txn("UC-08", "overcharge within estimate")
    txn, paid, _ = book(t, BUYERS["nila"], ECO)
    t.step("update (start)", bap("start", {"txn": txn}))
    cpo("cms-offline", {"txn": txn, "extraKwh": 0.3})
    r = t.step("update (stop)", bap("stop", {"txn": txn}))
    c = r["message"]["contract"]
    t.check(any("Overcharge" in x["description"] for x in money(c)["components"]), "overcharge not itemised")
    t.check(money(c)["value"] == paid and refunds(c) == 0, "overcharge within estimate should leave nothing to refund")
    t.step("on_update (invoice)", bap("wait", {"txn": txn, "action": "on_update"}))
    return [t]


@uc("UC-09", "Early completion (battery full at 2.0 kWh): billed for 2.0, refund")
def uc09(it):
    t = Txn("UC-09", "early completion")
    txn, paid, _ = book(t, BUYERS["ravi"], ECO)
    c = charge(t, txn, 2.5, 2.0)
    t.check(refunds(c) == round(paid - bill_total(2.5, 2.0), 2), f"refund {refunds(c)} wrong")
    return [t]


@uc("UC-10", "Consumer cancellation: terms preview (try), free well before the slot, fee inside 30 min")
def uc10(it):
    out = []
    res = [r["id"] for c in CATALOGS for r in c["resources"] if r["id"] != ECO and any(r["id"] in o["resourceIds"] for o in c["offers"])]
    for name, start_in, late in (("cancel 2 h ahead", 120 + it * 300, False), ("cancel 10 min ahead", 10, True)):
        rid = res[(it + len(out)) % len(res)]
        fee = round(rate_of(rid) * 2.5 * 0.1, 2) if late else 0.0
        t = Txn("UC-10", name)
        txn, paid, _ = book(t, BUYERS["asha"], rid, start_in=start_in, length=60)
        r = t.step("cancel (try: preview)", bap("cancel", {"txn": txn, "preview": True}))
        prev = r["message"]["contract"]
        t.check(prev["settlements"][-1]["settlementAttributes"]["beckn:amount"]["value"] == round(paid - fee, 2), "previewed refund wrong")
        r = t.step("cancel", bap("cancel", {"txn": txn}))
        c = r["message"]["contract"]
        t.check(c["status"]["code"] == "CANCELLED" and refunds(c) == round(paid - fee, 2), f"refund {refunds(c)} != {round(paid - fee, 2)}")
        out.append(t)
    return out


@uc("UC-11", "CPO cancellation: charger fault, unsolicited on_cancel with a full refund")
def uc11(it):
    t = Txn("UC-11", "CPO cancels")
    txn, paid, _ = book(t, BUYERS["kiran"], ECO, start_in=900 + it * 200)
    cpo("cpo-cancel", {"txn": txn})
    r = t.step("on_cancel (unsolicited)", bap("wait", {"txn": txn, "action": "on_cancel"}))
    c = r["message"]["contract"]
    t.check(c["status"]["code"] == "CANCELLED" and c["descriptor"]["code"] == "CPO_CHARGER_FAULT", "not cancelled by CPO")
    t.check(refunds(c) == paid, "CPO cancellation must refund in full")
    return [t]


@uc("UC-12", "Support lifecycle: connector stuck after charging, ticket opened, resolved by the CPO")
def uc12(it):
    t = Txn("UC-12", "support ticket")
    txn, paid, _ = book(t, BUYERS["meera"], ECO)
    charge(t, txn, 2.5, 2.5)
    r = t.step("support", bap("support", {"txn": txn, "code": "CONNECTOR_FAULT", "name": "Connector not releasing",
                                          "text": "Charging stopped but the connector is still locked."}))
    tid = r["message"]["support"]["descriptor"]["name"].split()[1]
    cpo("resolve-ticket", {"ticketId": tid, "text": "Connector released remotely."})
    r = t.step("on_support (resolved, unsolicited)", bap("wait", {"txn": txn, "action": "on_support"}))
    t.check(r["message"]["support"]["descriptor"]["code"] == "RESOLVED", "ticket not resolved")
    return [t]


@uc("UC-13", "Catalog publishing (business): CPO publishes a new site, discovery finds it")
def uc13(it):
    t = Txn("UC-13", "publish and discover")
    site = [77.6700, 12.8450]  # Electronic City
    rid = f"IND*ecopower-charging*cs-09*IN*ECO*ELC*0{it % 10}*CCS2*A*CCS2-A"
    base = next(c for c in CATALOGS if c["provider"]["id"] == "ecopower-charging")
    res = json.loads(json.dumps(base["resources"][0]))
    res["id"] = rid
    res["descriptor"]["name"] = "DC Fast Charger - Electronic City"
    res["resourceAttributes"]["chargingStation"]["id"] = "IN-ECO-ELC-STATION-09"
    res["resourceAttributes"]["chargingStation"]["serviceLocation"] = {"geo": {"type": "Point", "coordinates": site},
        "address": {"streetAddress": "Phase 1, Electronic City", "addressLocality": "Bengaluru", "addressRegion": "Karnataka",
                    "postalCode": "560100", "addressCountry": "IN"}}
    off = json.loads(json.dumps(base["offers"][0]))
    off["id"], off["resourceIds"] = f"offer-elc-{it}", [rid]
    off["considerations"][0]["id"] = f"price-offer-elc-{it}"
    cat = {"id": f"catalog-ev-ecopower-elc-{it}", "descriptor": {"name": "EcoPower Electronic City"},
           "provider": {**base["provider"], "availableAt": [{"geo": {"type": "Point", "coordinates": site}}]},
           "resources": [res], "offers": [off]}
    r = cpo("publish-catalog", {"catalog": cat})
    t.steps.append({"action": "catalog/publish", "ok": r.get("status") == 200, "ms": None, "error": None})
    t.check(r.get("status") == 200, f"catalog/publish not ACKed: {r}")
    time.sleep(1.0)
    st = call(args.cpo, "/api/state")
    t.check(any(x["results"][0]["catalogId"] == cat["id"] and x["results"][0]["status"] == "ACCEPTED" for x in st["published"]),
            "catalog/on_publish ACCEPTED not received")
    t.steps.append({"action": "catalog/on_publish", "ok": True, "ms": None, "error": None})
    r = t.step("discover (new site)", bap("discover", {"intent": {"spatial": [{"op": "S_DWITHIN", "targets": "$.catalogs[*].provider.availableAt[*].geo",
                                                                               "geometry": {"type": "Point", "coordinates": site}, "distanceMeters": 500}]}}))
    t.check(rid in found(r), "published charger not discoverable")
    return [t]


@uc("UC-14", "Guard rails: invalid state transitions are refused with business errors")
def uc14(it):
    t = Txn("UC-14", "invalid transitions")
    txn, paid, _ = book(t, BUYERS["dev"], ECO)
    r = t.step("update (stop before start)", bap("stop", {"txn": txn}), expect_ok=False)
    t.check(r["error"]["code"] == "BIZ_INVALID_STATE_TRANSITION", f"wrong error {r['error']}")
    charge(t, txn, 2.5, 2.5)
    r = t.step("cancel after completion", bap("cancel", {"txn": txn}), expect_ok=False)
    t.check(r["error"]["code"] == "BIZ_INVALID_STATE_TRANSITION", f"wrong error {r['error']}")
    return [t]


# ---------------------------------------------------------------- runner
def main():
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    results = []
    for it in range(args.iterations):
        call(args.cpo, "/admin/reset", {})  # each iteration starts from the shipped catalog
        for code, (title, fn) in UCS.items():
            if only and code not in only:
                continue
            CURRENT.clear()
            try:
                fn(it)
            except Exception as e:  # the transaction in progress is the one that failed
                t = CURRENT[-1] if CURRENT else Txn(code, "setup")
                t.ok = False
                t.reason = str(e) if isinstance(e, Fail) else f"{e!r} {traceback.format_exc(limit=3)}"
            txns = list(CURRENT)
            for t in txns:
                results.append({"uc": code, "title": title, "iteration": it, "name": t.name, "transactionId": t.id,
                                "ok": t.ok, "reason": t.reason, "steps": t.steps,
                                "seconds": round(time.time() - t.t0, 2)})
            status = "PASS" if all(t.ok for t in txns) else "FAIL"
            print(f"[{it}] {status} {code} {title} ({len(txns)} txn)" + ("" if status == "PASS" else f"  -> {txns[-1].reason[:300]}"), flush=True)
    report(results)
    return 0 if all(r["ok"] for r in results) else 1


def report(results):
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (out / f"run-{stamp}.json").write_text(json.dumps(results, indent=1))
    lat = {}
    for r in results:
        for s in r["steps"]:
            if s.get("ms"):
                lat.setdefault(s["action"].split(" ")[0], []).append(s["ms"])
    by_uc = {}
    for r in results:
        u = by_uc.setdefault(r["uc"], {"title": r["title"], "txn": 0, "ok": 0, "msgs": 0})
        u["txn"] += 1
        u["ok"] += r["ok"]
        u["msgs"] += sum(2 for s in r["steps"])  # one request + one callback per step
    cpo_state = call(args.cpo, "/api/state")
    lines = [f"# EV charging use-case run {stamp}", "",
             f"Transactions: **{sum(u['txn'] for u in by_uc.values())}**, passed **{sum(u['ok'] for u in by_uc.values())}**; "
             f"signed Beckn messages ~{sum(u['msgs'] for u in by_uc.values())}; CPO callbacks NACKed by ONIX: "
             f"{cpo_state.get('counters', {}).get('callbacks_nacked')}", "",
             "| Use case | Transactions | Passed | Title |", "|---|---|---|---|"]
    lines += [f"| {k} | {v['txn']} | {v['ok']} | {v['title']} |" for k, v in by_uc.items()]
    lines += ["", "| Action | n | p50 ms | p95 ms |", "|---|---|---|---|"]
    for a, v in sorted(lat.items()):
        v = sorted(v)
        lines.append(f"| {a} | {len(v)} | {int(statistics.median(v))} | {v[min(len(v) - 1, int(len(v) * 0.95))]} |")
    fails = [r for r in results if not r["ok"]]
    if fails:
        lines += ["", "## Failures", ""] + [f"- {r['uc']} {r['name']}: {r['reason'][:400]}" for r in fails]
    (out / f"run-{stamp}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
