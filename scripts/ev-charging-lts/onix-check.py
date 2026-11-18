#!/usr/bin/env python3
"""POST every LTS example in a folder through the local ONIX devkit stack and report
ACK/NACK per file. Requests go to the BAP caller, callbacks and catalog publishing to
the BPP caller, so each payload is signed and schema-validated (core spec + attribute
packs) exactly as on a live network. Context ids, network id and URIs are rewritten to
the devkit's registered test participants; nothing else in the payload is changed.

Usage: onix-check.py <examples dir> [bap caller url] [bpp caller url]
"""
import datetime, json, pathlib, sys, urllib.request, urllib.error, uuid

root = pathlib.Path(sys.argv[1])
BAP = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8081/bap/caller"
BPP = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8082/bpp/caller"


def prep(d, txn):
    c = d["context"]
    c["timestamp"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    c["messageId"] = str(uuid.uuid4())
    c["transactionId"] = txn
    c["networkId"] = "nfh.global/testnet-evcharging"
    if c["action"].startswith("catalog/"):
        c["bppId"], c["bppUri"] = "bpp.example.com", "http://beckn-router:9000/bpp/receiver"
        return d
    c["bapId"], c["bapUri"] = "bap.example.com", "http://beckn-router:9000/bap/receiver"
    if c["action"] != "discover":
        c["bppId"], c["bppUri"] = "bpp.example.com", "http://beckn-router:9000/bpp/receiver"
    return d


def post(url, d):
    req = urllib.request.Request(url, json.dumps(d).encode(), {"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body.decode()[:300]}


fails = 0
files = sorted(f for f in root.rglob("*.json"))
txn = str(uuid.uuid4())
for f in files:
    d = json.load(open(f))
    if not isinstance(d, dict) or "context" not in d:
        continue
    a = d["context"]["action"]
    url = (BPP if a.startswith("on_") or a.startswith("catalog/") else BAP) + "/" + a
    code, body = post(url, prep(d, txn))
    msg = (body.get("message") or {}) if isinstance(body, dict) else {}
    ok = code == 200 and msg.get("status") == "ACK"
    err = msg.get("error") or {}
    fails += 0 if ok else 1
    detail = "" if ok else f"{err.get('code', code)}: {err.get('message', body)}"[:260]
    print(f"{'PASS' if ok else 'FAIL'}  {str(f.relative_to(root)):70} {a:18} {detail}")
print(f"\n{fails} failing of {len(files)}")
sys.exit(1 if fails else 0)
