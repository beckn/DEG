#!/usr/bin/env python3
"""EV charging consumer app (BAP) reference app, Beckn 2.0 LTS.

A JSON API (and a small web UI on /) that an EV driver app would sit on. Each API call
sends one Beckn request through the ONIX BAP caller and waits for the matching callback
on /api/bap-webhook/<action>; unsolicited callbacks (payment received, power cut,
CPO cancellation, invoice ready, ticket resolved) can be awaited with /api/wait.
"""
import copy
import json
import os
import pathlib
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "common"))
import beckn  # noqa: E402

PORT = int(os.environ.get("PORT", "3001"))
BAP_CALLER = os.environ.get("ONIX_BAP_CALLER", "http://onix-bap:8081/bap/caller")
BAP_ID = os.environ.get("BAP_ID", "bap.example.com")
BAP_URI = os.environ.get("BAP_URI", "http://beckn-router:9000/bap/receiver")
WAIT_S = float(os.environ.get("CALLBACK_TIMEOUT_S", "20"))

REC = beckn.Recorder()
COND = threading.Condition()
SESSIONS = {}  # txn -> {"events": [...], "contract": {...}, "bppId", "bppUri", "catalogs", "buyer"}


def session(txn):
    return SESSIONS.setdefault(txn, {"txn": txn, "events": []})


def request(action, txn, message, s=None, try_=None):
    s = s or session(txn)
    ctx = {"version": beckn.VERSION, "action": action, "networkId": beckn.NETWORK_ID,
           "bapId": BAP_ID, "bapUri": BAP_URI, "transactionId": txn, "messageId": beckn.new_id(),
           "timestamp": beckn.now_iso(), "ttl": "PT30S"}
    if action != "discover":
        ctx.update(bppId=s["bppId"], bppUri=s["bppUri"])
    if try_ is not None:
        ctx["try"] = try_
    body = {"context": ctx, "message": message}
    t0 = time.time()
    code, resp = beckn.post_json(f"{BAP_CALLER}/{action}", body)
    ok = code == 200 and (resp.get("message") or {}).get("status") == "ACK"
    REC.add("out", action, body, "ACK" if ok else f"NACK {code}", int((time.time() - t0) * 1000))
    if not ok:
        return {"ok": False, "stage": "send", "status": code, "response": resp}
    cb = wait_for(txn, "on_" + action, message_id=ctx["messageId"])
    if cb is None:
        return {"ok": False, "stage": "callback", "error": f"no on_{action} within {WAIT_S}s", "messageId": ctx["messageId"]}
    cb["latencyMs"] = int((time.time() - t0) * 1000)
    return cb


def wait_for(txn, action, message_id=None, after=None, timeout=None):
    deadline = time.time() + (timeout or WAIT_S)
    with COND:
        while True:
            for ev in session(txn)["events"]:
                if ev["action"] != action or ev.get("consumed"):
                    continue
                if message_id and ev["messageId"] != message_id:
                    continue
                if after and ev["at"] <= after:
                    continue
                ev["consumed"] = True
                return {"ok": "error" not in ev["body"], "action": action, "error": ev["body"].get("error"),
                        "message": ev["body"].get("message"), "context": ev["body"].get("context")}
            left = deadline - time.time()
            if left <= 0:
                return None
            COND.wait(left)


def on_callback(action, body):
    ctx = body.get("context") or {}
    txn = ctx.get("transactionId")
    REC.add("in", action, body)
    with COND:
        s = session(txn)
        s["events"].append({"action": action, "messageId": ctx.get("messageId"), "at": beckn.now_iso(), "body": body})
        msg = body.get("message") or {}
        if "contract" in msg and not body.get("error") and not ctx.get("try"):
            s["contract"] = msg["contract"]
        COND.notify_all()


# ---------------------------------------------------------------- consumer operations
def commitments_of(s):
    return copy.deepcopy(s["contract"]["commitments"])


def ref_contract(s, **extra):
    c = {"id": s["contract"].get("id"), "commitments": commitments_of(s)}
    c.update(extra)
    return {k: v for k, v in c.items() if v is not None}


def buyer_participant(b):
    return {"id": b["id"], "descriptor": {"name": b["name"]},
            "participantAttributes": beckn.pack("consumer", "Consumer", {
                "role": "BUYER", "person": {"id": b["id"], "name": b["name"], "telephone": b["phone"], "email": b["email"]}})}


def op_discover(body):
    txn = body.get("txn") or beckn.new_id()
    r = request("discover", txn, {"intent": body["intent"]})
    if r.get("message"):
        session(txn)["catalogs"] = r["message"].get("catalogs", [])
    return {"txn": txn, **r}


def op_select(body):
    txn = body.get("txn") or beckn.new_id()
    s = session(txn)
    cat = body["catalog"]
    s.update(bppId=cat.get("bppId"), bppUri=cat.get("bppUri"), buyer=body["buyer"])
    rid, kwh = body["resourceId"], float(body.get("kwh", 2.5))
    offer = next(o for o in cat["offers"] if rid in o.get("resourceIds", []) and (not body.get("offerId") or o["id"] == body["offerId"]))
    contract = {
        "status": {"code": "DRAFT"},
        "participants": [{"id": cat["provider"]["id"], "descriptor": cat["provider"]["descriptor"]},
                         buyer_participant(body["buyer"])],
        "commitments": [{"id": "commitment-001", "status": {"descriptor": {"code": "DRAFT"}},
                         "resources": [{"id": rid, "quantity": {"unitText": "Kilowatt Hour", "unitCode": "KWH", "unitQuantity": kwh}}],
                         "offer": {"id": offer["id"], "resourceIds": offer["resourceIds"]}}],
    }
    if body.get("startTime"):
        contract["contractAttributes"] = beckn.session_attrs(
            preferences={"startTime": body["startTime"], "endTime": body["endTime"]})
    return {"txn": txn, **request("select", txn, {"contract": contract})}


def op_init(body):
    s = session(body["txn"])
    c = copy.deepcopy(s["contract"])
    total = c["consideration"][0]["considerationAttributes"]["value"]
    c["settlements"] = [{"id": "settlement-001", "considerationId": "consideration-001", "status": "DRAFT",
                         "settlementAttributes": beckn.payment_attrs("INITIATED", total, body.get("payment", "BPP"))}]
    return request("init", body["txn"], {"contract": c})


def op_pay_bap(body):
    """BAP-collected payment: the consumer pays the BAP; recorded on the contract for confirm."""
    s = session(body["txn"])
    a = s["contract"]["settlements"][0]["settlementAttributes"]
    a.update({"beckn:paymentStatus": "COMPLETED", "beckn:txnRef": f"BAP-UPI-{body['txn'][:8]}", "beckn:paidAt": beckn.now_iso()})
    s["contract"]["settlements"][0]["status"] = "COMPLETE"
    return {"ok": True, "paid": a["beckn:amount"]["value"]}


def op_confirm(body):
    s = session(body["txn"])
    return request("confirm", body["txn"], {"contract": copy.deepcopy(s["contract"])})


def session_update(body, status):
    s = session(body["txn"])
    perf = [{"id": "fulfillment-001", "status": {"code": status}, "commitmentIds": ["commitment-001"],
             "performanceAttributes": beckn.session_attrs(sessionStatus=status)}]
    return request("update", body["txn"], {"contract": ref_contract(s, performance=perf)})


def op_status(body):
    return request("status", body["txn"], {"contract": ref_contract(session(body["txn"]))})


def op_track(body):
    s = session(body["txn"])
    return request("track", body["txn"], {"tracking": {"contract": ref_contract(s), "status": "ACTIVE",
                                                       "url": f"https://{BAP_ID}/sessions/{body['txn']}"}})


def op_cancel(body):
    s = session(body["txn"])
    c = ref_contract(s, descriptor={"code": body.get("reason", "USER_CHANGED_PLANS"), "shortDesc": body.get("text", "Plans changed")})
    return request("cancel", body["txn"], {"contract": c}, try_=True if body.get("preview") else None)


def op_rate(body):
    s = session(body["txn"])
    return request("rate", body["txn"], {"ratingInputs": [{
        "target": {"id": s["contract"]["id"], "descriptor": {"code": "CONTRACT", "name": "Charging session"}},
        "range": {"bestRating": 5, "worstRating": 1, "ratingValue": body.get("value", 5)},
        **({"feedbackFormSubmission": {"data": {"comments": body["comments"]}}} if body.get("comments") else {})}]})


def op_support(body):
    s = session(body["txn"])
    b = s["buyer"]
    return request("support", body["txn"], {"support": {
        "orderId": s["contract"]["id"],
        "descriptor": {"code": body.get("code", "GENERAL"), "name": body.get("name", "Help with charging session"),
                       "shortDesc": body.get("text", "")},
        "channels": [beckn.pack("support", "SupportInfo", {"name": b["name"], "telephone": b["phone"], "email": b["email"],
                                                           "channels": ["PHONE", "WHATSAPP"]})]}})


def op_wait(body):
    r = wait_for(body["txn"], body["action"], after=body.get("after"), timeout=body.get("timeout"))
    return r or {"ok": False, "error": f"no {body['action']} within timeout"}


OPS = {"discover": op_discover, "select": op_select, "init": op_init, "pay": op_pay_bap, "confirm": op_confirm,
       "status": op_status, "start": lambda b: session_update(b, "ACTIVE"), "stop": lambda b: session_update(b, "STOP"),
       "track": op_track, "cancel": op_cancel, "rate": op_rate, "support": op_support, "wait": op_wait}

UI = pathlib.Path(__file__).parent / "ui.html"


class Handler(beckn.JsonHandler):
    routes = {("POST", "/api/bap-webhook"): "webhook", ("POST", "/api/"): "api", ("GET", "/api/health"): "health",
              ("GET", "/api/session"): "get_session", ("GET", "/api/messages"): "messages", ("GET", "/"): "ui"}

    def webhook(self, action, body):
        on_callback(action, body)
        return 200, beckn.ack((body.get("context") or {}).get("messageId")), "application/json"

    def api(self, op, body):
        if op not in OPS:
            return 404, {"error": f"unknown op {op}"}, "application/json"
        return 200, OPS[op](body or {}), "application/json"

    def health(self, _, __):
        return 200, {"status": "ok", "service": "ev-consumer-app"}, "application/json"

    def get_session(self, txn, _):
        s = SESSIONS.get(txn) or {}
        return 200, {"txn": txn, "contract": s.get("contract"),
                     "events": [{"action": e["action"], "at": e["at"], "error": e["body"].get("error")} for e in s.get("events", [])]}, "application/json"

    def messages(self, _, __):
        return 200, REC.dump(), "application/json"

    def ui(self, _, __):
        return 200, UI.read_bytes(), "text/html"


if __name__ == "__main__":
    beckn.serve(Handler, PORT)
