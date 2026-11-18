"""Shared Beckn 2.0 LTS helpers for the EV charging reference apps.

Standard library only. Both apps talk to the network exclusively through their ONIX
adapter (the BAP caller or the BPP caller), so every message is signed, registry-checked
and schema-validated exactly as on a live network.
"""
import datetime
import json
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "2.0.0"
NETWORK_ID = "nfh.global/testnet-evcharging"
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


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_iso(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def new_id(prefix=""):
    return f"{prefix}{uuid.uuid4()}"


def ack(message_id=None):
    return {"message": {"status": "ACK", "messageId": message_id}}


def post_json(url, body, timeout=30):
    """POST JSON; return (status, parsed body). Never raises on HTTP errors."""
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        raw = r.read()
        return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw.decode(errors="replace")[:500]}
    except Exception as e:  # connection refused, timeout
        return 0, {"error": str(e)}


def pack(key, type_name, body):
    out = {"@context": CTX[key], "@type": type_name}
    out.update(body)
    return out


def price_spec(currency, value, components=None, applicable=None):
    body = {"currency": currency, "value": round(value, 2)}
    if applicable:
        body["applicableQuantity"] = applicable
    if components:
        body["components"] = [{"type": t, "value": round(v, 2), "currency": currency, "description": d}
                              for t, v, d in components]
    return pack("price", "PriceSpecification", body)


def session_attrs(**fields):
    return pack("session", "ChargingSession", {k: v for k, v in fields.items() if v is not None})


def payment_attrs(status, amount, beneficiary, **extra):
    body = {"beckn:paymentStatus": status, "beckn:amount": {"currency": "INR", "value": round(amount, 2)},
            "beckn:beneficiary": beneficiary}
    body.update({f"beckn:{k}": v for k, v in extra.items() if v is not None})
    return pack("payment", "Payment", body)


class Recorder:
    """Thread-safe log of every message an app sent or received (for metrics and lint)."""

    def __init__(self, limit=5000):
        self.lock = threading.Lock()
        self.items = []
        self.limit = limit

    def add(self, direction, action, body, status=None, ms=None):
        with self.lock:
            self.items.append({"at": now_iso(), "direction": direction, "action": action,
                               "transactionId": (body.get("context") or {}).get("transactionId"),
                               "messageId": (body.get("context") or {}).get("messageId"),
                               "status": status, "ms": ms, "body": body})
            del self.items[:-self.limit]

    def dump(self):
        with self.lock:
            return list(self.items)


class JsonHandler(BaseHTTPRequestHandler):
    """Minimal JSON router. Subclasses set `routes = {(method, prefix): handler_name}`."""

    routes = {}
    server_version = "ev-reference-app/1.0"

    def log_message(self, fmt, *args):  # quiet; apps log what matters themselves
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        return json.loads(raw) if raw else {}

    def _dispatch(self, method):
        path = self.path.split("?")[0]
        for (m, prefix), name in sorted(self.routes.items(), key=lambda kv: -len(kv[0][1])):
            if m == method and path.startswith(prefix):
                try:
                    body = self._body() if method == "POST" else None
                    code, out, ctype = getattr(self, name)(path[len(prefix):].strip("/"), body)
                except Exception as e:  # keep the server alive; report the failure
                    code, out, ctype = 500, {"error": repr(e)}, "application/json"
                return self._send(code, out, ctype)
        self._send(404, {"error": f"no route for {method} {path}"})

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


def serve(handler, port):
    srv = ThreadingHTTPServer(("0.0.0.0", port), handler)
    srv.daemon_threads = True
    print(f"listening on :{port}", flush=True)
    srv.serve_forever()


def later(fn, *args, delay=0.05):
    """Run fn in the background after the synchronous ACK has been returned."""
    def run():
        time.sleep(delay)
        try:
            fn(*args)
        except Exception as e:
            print(f"background task failed: {e!r}", flush=True)
    threading.Thread(target=run, daemon=True).start()
