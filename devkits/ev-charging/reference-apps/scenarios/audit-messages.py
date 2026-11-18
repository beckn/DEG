#!/usr/bin/env python3
"""Audit every Beckn message the two reference apps sent and received.

Pulls the message logs from both apps, counts messages by action and outcome, and
writes each payload to a folder so it can be linted against the LTS core schema
(core-lint.py) and replayed through ONIX if needed.

Usage: audit-messages.py [--bap http://localhost:3001] [--cpo http://localhost:3002] [--dump <dir>]
"""
import argparse
import collections
import json
import pathlib
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--bap", default="http://localhost:3001")
ap.add_argument("--cpo", default="http://localhost:3002")
ap.add_argument("--dump", default="")
args = ap.parse_args()

def get(url):
    return json.loads(urllib.request.urlopen(url, timeout=30).read())

rows = []
for app, base in (("consumer", args.bap), ("cpo", args.cpo)):
    for m in get(base + "/api/messages"):
        rows.append((app, m))
counts = collections.Counter()
outcome = collections.Counter()
txns = set()
for app, m in rows:
    key = f"{app} {m['direction']} {m['action']}"
    counts[key] += 1
    if m["direction"] == "out":
        outcome["ACK" if m["status"] == "ACK" else "NACK"] += 1
    txns.add(m.get("transactionId"))
print(f"messages logged: {len(rows)} (consumer {sum(1 for a, _ in rows if a == 'consumer')}, cpo {sum(1 for a, _ in rows if a == 'cpo')}); "
      f"transactions: {len(txns)}; sent ACK {outcome['ACK']}, NACK {outcome['NACK']}")
for k, v in sorted(counts.items()):
    print(f"  {v:5}  {k}")
if args.dump:
    d = pathlib.Path(args.dump)
    d.mkdir(parents=True, exist_ok=True)
    for i, (app, m) in enumerate(rows):
        if m["direction"] == "out":  # what each app put on the wire
            (d / f"{i:05d}-{app}-{m['action'].replace('/', '_')}.json").write_text(json.dumps(m["body"]))
    print(f"wrote sent payloads to {d}")
