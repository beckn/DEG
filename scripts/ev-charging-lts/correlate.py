#!/usr/bin/env python3
"""Give the generated EV examples LTS-correct message correlation.

LTS: a callback carries the messageId of the request it answers, and every new
interaction gets a new messageId. This pass assigns deterministic messageIds: each
request and the callback(s) answering it share one; every other file (unsolicited
callbacks, alternative requests) gets its own. A callback timestamped before its
request is moved to two seconds after it.

Usage: correlate.py <examples dir>
"""
import datetime
import json
import pathlib
import sys
import uuid

root = pathlib.Path(sys.argv[1])
NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/beckn/DEG/examples/ev-charging/v2")

# request file -> callbacks that answer it (alternative answers share the request's id)
PAIRS = {
    "01_discover/discovery-by-EVSE": ["02_on_discover/ev-charging-specific-evse-catalog"],
    "01_discover/discovery-within-a-circular-boundary": ["02_on_discover/ev-charging-discovery-catalog"],
    "03_select/ev-charging-select": ["04_on_select/ev-charging-on-select", "04_on_select/ev-charging-on-select-slot-unavailable",
                                     "04_on_select/ev-charging-on-select-outstanding-dues"],
    "05_init/ev-charging-bap-payment-init": ["06_on_init/ev-charging-bap-payment-on-init"],
    "05_init/ev-charging-bpp-payment-init": ["06_on_init/ev-charging-bpp-payment-on-init"],
    "07_confirm/ev-charging-confirm": ["08_00_on_confirm/ev-charging-on-confirm"],
    "08_01_status/ev-charging-connector-status": ["08_02_on_status/ev-charging-connector-on-status"],
    "09_update/ev-charging-01-session-start-update": ["10_on_update/ev-charging-session-on-update",
                                                       "10_on_update/ev-charging-session-start-rejected-on-update"],
    "11_status/ev-charging-session-track": ["12_on_status/ev-charging-session-on-track"],
    "14_01_update/ev-charging-session-end-update": ["14_02_on_update/ev-charging-session-complete-on-update",
                                                     "14_02_on_update/ev-charging-session-overcharge-on-update",
                                                     "14_02_on_update/ev-charging-session-undercharge-on-update"],
    "15_rating/ev-charging-session-rating": ["16_on_rating/ev-charging-session-on-rating"],
    "17_support/ev-charging-session-support": ["18_on_support/ev-charging-session-on-support"],
    "19_cancel/ev-charging-cancel-reserved-slot": ["20_on_cancel/ev-charging-bpp-reservation-on-cancel"],
    "19_cancel/ev-charging-cancel-preview": ["20_on_cancel/ev-charging-cancel-preview-on-cancel"],
    "21_track/ev-charging-session-track": ["22_on_track/ev-charging-session-on-track"],
    "23_catalog_publish/ev-charging-catalog-publish": ["24_catalog_on_publish/ev-charging-catalog-on-publish"],
}


def ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def load(rel):
    return json.load(open(root / f"{rel}.json"))


def save(rel, d):
    (root / f"{rel}.json").write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")


answered = {cb for cbs in PAIRS.values() for cb in cbs}
files = sorted(str(f.relative_to(root))[:-5] for f in root.rglob("*.json"))
for rel in files:
    if rel in answered:
        continue
    d = load(rel)
    d["context"]["messageId"] = str(uuid.uuid5(NS, rel))
    save(rel, d)
    for cb in PAIRS.get(rel, []):
        if not (root / f"{cb}.json").exists():
            raise SystemExit(f"missing callback {cb} for {rel}")
        c = load(cb)
        c["context"]["messageId"] = d["context"]["messageId"]
        if ts(c["context"]["timestamp"]) <= ts(d["context"]["timestamp"]):
            c["context"]["timestamp"] = (ts(d["context"]["timestamp"]) + datetime.timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        save(cb, c)
ids = {}
for rel in files:
    ids.setdefault(load(rel)["context"]["messageId"], []).append(rel)
shared = {k: v for k, v in ids.items() if len(v) > 1}
bad = [v for v in shared.values() if sum(1 for r in v if r not in answered) != 1]
print(f"{len(files)} files, {len(ids)} messageIds, {len(shared)} request/callback groups" + (f", BAD: {bad}" if bad else ""))
sys.exit(1 if bad else 0)
