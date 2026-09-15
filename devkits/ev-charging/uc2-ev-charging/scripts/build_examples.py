#!/usr/bin/env python3
"""Build the uc2-ev-charging example payloads and sandbox fixtures.

Every payload is derived from one catalog and one set of scenario facts, and
each step is built from the previous one exactly as DESIGN.md §6 prescribes
(select copies the offer, on_select adds the quote, init/confirm copy the
previous contract, on_confirm opens the ledger). Edit the facts here and
re-run instead of hand-editing JSON, so the flow stays consistent.

Usage (from anywhere):
  python3 devkits/ev-charging/uc2-ev-charging/scripts/build_examples.py
"""

import copy
import sys
from pathlib import Path

UC_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = UC_ROOT.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from generate_postman_collection import _format_payload  # noqa: E402

RAW = "https://raw.githubusercontent.com/ameetdesh/DEG/refs/heads/main/specification"
NFH = "https://schema.nfh.global"

CTX = {
    "service": f"{RAW}/schema/EvChargingService/v2.0/context.jsonld",
    "offer": f"{RAW}/schema/EvChargingOffer/v3.0/context.jsonld",
    "commitment": f"{RAW}/schema/EvChargingCommitment/v1.0/context.jsonld",
    "session": f"{RAW}/schema/EvChargingSession/v3.0/context.jsonld",
    "contract": f"{NFH}/DEGContract/v2.0/context.jsonld",
}

NETWORK = "nfh.global/testnet-deg"
BAP_ID, BPP_ID = "bap.example.com", "bpp.example.com"
POLICY = {"url": f"{RAW}/policies/ev-charging-contractpolicy.rego", "queryPath": "data.deg.contracts.ev_charging"}

# ── Catalog ────────────────────────────────────────────────────────────────

POOL = {
    "id": "ecopower-btm-ccs2-dc60",
    "descriptor": {"name": "BTM Hub · CCS2 DC up to 60 kW", "shortDesc": "4 stalls, one virtual queue"},
    "resourceAttributes": {
        "@context": CTX["service"],
        "@type": "ChargingService",
        "connectorType": "CCS2",
        "maxPowerKW": 60,
        "powerType": "DC",
        "chargingSpeed": "FAST",
        "vehicleType": "4-WHEELER",
        "reservationSupported": True,
        "chargingStation": {
            "id": "IN-ECO-BTM-01",
            "serviceLocation": {
                "geo": {"type": "Point", "coordinates": [77.6104, 12.9153]},
                "address": {"streetAddress": "EcoPower BTM Hub, 100 Ft Rd", "addressLocality": "Bengaluru", "addressRegion": "Karnataka", "postalCode": "560076", "addressCountry": "IN"},
            },
        },
    },
}


def contract_template():
    return {
        "@context": CTX["contract"],
        "@type": "DEGContract",
        "roles": [{"role": "cpo", "participantId": BPP_ID}, {"role": "driver", "participantId": None}],
        "policy": dict(POLICY),
    }


COMMON_TERMS = {"currency": "INR", "energyPerKWh": 18, "occupancyPerMin": 2, "idlePerMin": 10, "graceMin": 5, "maxDemotions": 2, "gridDelayCreditPerMin": 1}

WALK_IN_OFFER = {
    "id": "ecopower-btm-walk-in",
    "descriptor": {"name": "Walk-in", "shortDesc": "Join the queue now"},
    "resourceIds": [POOL["id"]],
    "offerAttributes": {"@context": CTX["offer"], "@type": "ChargingOffer", "mode": "WALK_IN", "terms": dict(COMMON_TERMS), "contractAttributes": contract_template()},
}

RESERVATION_OFFER = {
    "id": "ecopower-btm-reservation",
    "descriptor": {"name": "Reservation", "shortDesc": "Book a start time at least an hour ahead"},
    "resourceIds": [POOL["id"]],
    "offerAttributes": {
        "@context": CTX["offer"],
        "@type": "ChargingOffer",
        "mode": "RESERVATION",
        "terms": {**COMMON_TERMS, "reservation": {"fee": 100, "cancelBeforeMin": 60, "cpoDelayCreditPerMin": 5, "liabilityCap": 500}},
        "contractAttributes": contract_template(),
    },
}

CATALOG = {
    "id": "ecopower-btm-catalog",
    "descriptor": {"name": "EcoPower BTM Hub"},
    "bppId": BPP_ID,
    "bppUri": f"https://{BPP_ID}/bpp/receiver",
    "provider": {"id": "ecopower", "descriptor": {"name": "EcoPower Charging Pvt Ltd"}},
    "resources": [POOL],
    "offers": [WALK_IN_OFFER, RESERVATION_OFFER],
}

# ── Scenario facts ─────────────────────────────────────────────────────────

RESERVATION = {
    "txn": "7f1c2b9e-4d3a-4e8f-9b61-2a5c8d0e1f01",
    "contract_id": "c3a4e5f6-1b2c-4d3e-8f90-a1b2c3d4e5f6",
    "offer": RESERVATION_OFFER,
    "kwh_needed": 30,
    "vehicle": {"maxChargeKW": 60, "socPercent": 22},
    "reservedStart": "2026-10-02T18:00:00Z",
    "quote": {"promisedKW": 60, "estimatedStart": {"from": "2026-10-02T18:00:00Z", "to": "2026-10-02T18:10:00Z"}},
    "times": {"select": "2026-10-02T12:00:00Z", "on_select": "2026-10-02T12:00:02Z", "init": "2026-10-02T12:01:00Z", "on_init": "2026-10-02T12:01:02Z", "confirm": "2026-10-02T12:05:00Z", "on_confirm": "2026-10-02T12:05:02Z"},
}

WALK_IN = {
    "txn": "2e8d4c6a-9f1b-4a7e-b3c5-6d0e8f2a4b02",
    "contract_id": "d4b5f6a7-2c3d-4e5f-9a01-b2c3d4e5f6a7",
    "offer": WALK_IN_OFFER,
    "kwh_needed": 25,
    "vehicle": {"maxChargeKW": 50, "socPercent": 35},
    "quote": {"promisedKW": 50, "estimatedStart": {"from": "2026-10-02T10:15:00Z", "to": "2026-10-02T10:30:00Z"}},
    "times": {"select": "2026-10-02T10:00:00Z", "on_select": "2026-10-02T10:00:02Z", "init": "2026-10-02T10:00:30Z", "on_init": "2026-10-02T10:00:32Z", "confirm": "2026-10-02T10:01:00Z", "on_confirm": "2026-10-02T10:01:02Z"},
}

STALL_A1, STALL_A2 = "IN*ECO*E01BTM*A1", "IN*ECO*E01BTM*A2"


def row(at, state, **fields):
    return {"at": at, "state": state, **fields}


RESERVATION_LEDGER_ASSIGNED = [
    row("2026-10-02T12:05:00Z", "QUEUED"),
    row("2026-10-02T18:12:00Z", "ASSIGNED", stallId=STALL_A1),
]

RESERVATION_LEDGER_SETTLED = RESERVATION_LEDGER_ASSIGNED + [
    row("2026-10-02T18:15:00Z", "CHARGING", kWh=10.0),
    row("2026-10-02T18:25:00Z", "LIMITED_BY_GRID", kWh=5.0, eventId="BESCOM-DR-2026-10-02-1825"),
    row("2026-10-02T18:35:00Z", "LIMITED_BY_CPO", kWh=0),
    row("2026-10-02T18:39:00Z", "CHARGING", kWh=16.0),
    row("2026-10-02T18:55:00Z", "IDLE"),
    row("2026-10-02T19:04:00Z", "DEPARTED"),
]

RESERVATION_LEDGER_CANCELLED = [row("2026-10-02T12:05:00Z", "QUEUED"), row("2026-10-02T17:30:00Z", "CANCELLED")]

# Contract violation C2: NO_SHOW after 1 of 2 allowed demotions.
RESERVATION_LEDGER_EARLY_NO_SHOW = [
    row("2026-10-02T12:05:00Z", "QUEUED"),
    row("2026-10-02T18:00:00Z", "ASSIGNED", stallId=STALL_A1),
    row("2026-10-02T18:06:00Z", "QUEUED"),
    row("2026-10-02T18:10:00Z", "ASSIGNED", stallId=STALL_A2),
    row("2026-10-02T18:16:00Z", "NO_SHOW"),
]

WALK_IN_LEDGER_SETTLED = [
    row("2026-10-02T10:01:00Z", "QUEUED"),
    row("2026-10-02T10:20:00Z", "ASSIGNED", stallId=STALL_A1),
    row("2026-10-02T10:27:00Z", "QUEUED"),
    row("2026-10-02T10:31:00Z", "ASSIGNED", stallId=STALL_A2),
    row("2026-10-02T10:34:00Z", "CHARGING", kWh=24.0),
    row("2026-10-02T11:04:00Z", "IDLE"),
    row("2026-10-02T11:12:00Z", "DEPARTED"),
]

# ── Message builders ───────────────────────────────────────────────────────

_msg_counter = 0


def context(action, txn, timestamp, schema_keys, with_bpp=True):
    global _msg_counter
    _msg_counter += 1
    ctx = {"networkId": NETWORK, "version": "2.0.0", "action": action}
    if action != "catalog/publish":
        ctx.update({"bapId": BAP_ID, "bapUri": f"https://{BAP_ID}/bap/receiver"})
    if with_bpp:
        ctx.update({"bppId": BPP_ID, "bppUri": f"https://{BPP_ID}/bpp/receiver"})
    ctx.update({
        "transactionId": txn,
        "messageId": f"{txn[:24]}{_msg_counter:012d}",
        "timestamp": timestamp,
        "schemaContext": [CTX[k] for k in schema_keys],
    })
    return ctx


def select_contract(s):
    """select: offer copied verbatim, pool by reference + kWh, request added, contract template bound."""
    contract_attrs = copy.deepcopy(s["offer"]["offerAttributes"]["contractAttributes"])
    for r in contract_attrs["roles"]:
        if r["role"] == "driver":
            r["participantId"] = BAP_ID
    request = {"@context": CTX["commitment"], "@type": "ChargingCommitment", "vehicle": dict(s["vehicle"])}
    if "reservedStart" in s:
        request["reservedStart"] = s["reservedStart"]
    return {
        "status": {"code": "DRAFT"},
        "commitments": [{
            "status": {"descriptor": {"code": "DRAFT"}},
            "resources": [{"id": POOL["id"], "quantity": {"unitCode": "KWH", "unitQuantity": s["kwh_needed"]}}],
            "offer": copy.deepcopy(s["offer"]),
            "commitmentAttributes": request,
        }],
        "contractAttributes": contract_attrs,
    }


def on_select_contract(s):
    """on_select: the CPO names the commitment and adds its quote."""
    c = select_contract(s)
    commitment = {"id": "commitment-1", **c["commitments"][0]}
    commitment["commitmentAttributes"]["quote"] = copy.deepcopy(s["quote"])
    c["commitments"][0] = commitment
    return c


def active_contract(s, ledger, contract_status="ACTIVE", commitment_status="ACTIVE"):
    """on_confirm onward: contract id, statuses, and the session ledger."""
    c = on_select_contract(s)
    c = {"id": s["contract_id"], **c}
    c["status"] = {"code": contract_status}
    c["commitments"][0]["status"] = {"descriptor": {"code": commitment_status}}
    c["performance"] = [{
        "id": "session-1",
        "commitmentIds": ["commitment-1"],
        "performanceAttributes": {"@context": CTX["session"], "@type": "ChargingSession", "ledger": copy.deepcopy(ledger)},
    }]
    return c


TXN_KEYS = ["offer", "commitment", "contract"]
SESSION_KEYS = ["offer", "commitment", "session", "contract"]


def message(action, s, timestamp, contract, keys):
    return {"context": context(action, s["txn"], timestamp, keys), "message": {"contract": contract}}


def build():
    out = {}
    out["examples/publish-catalog.json"] = {
        "context": context("catalog/publish", "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c00", "2026-10-01T06:00:00Z", ["service", "offer", "contract"], with_bpp=True),
        "message": {"publishDirectives": [{"catalogId": CATALOG["id"], "catalogType": "REGULAR", "updateMode": "MERGE", "visibleTo": [NETWORK]}], "catalogs": [CATALOG]},
    }

    out["examples/discover-request.json"] = {
        "context": context("discover", "5b6c7d8e-9f0a-4b1c-8d2e-3f4a5b6c7d03", "2026-10-02T11:58:00Z", ["service", "offer"], with_bpp=False),
        "message": {"intent": {"filters": {"type": "jsonpath", "expression": "$.catalogs[*] ? (@.resources[*].resourceAttributes.connectorType == 'CCS2' && @.offers[*].offerAttributes.mode == 'RESERVATION')"}}},
    }

    r, w = RESERVATION, WALK_IN
    t = r["times"]
    out["examples/select-request.json"] = message("select", r, t["select"], select_contract(r), TXN_KEYS)
    out["examples/on-select-response.json"] = message("on_select", r, t["on_select"], on_select_contract(r), TXN_KEYS)
    out["examples/init-request.json"] = message("init", r, t["init"], on_select_contract(r), TXN_KEYS)
    out["examples/on-init-response.json"] = message("on_init", r, t["on_init"], on_select_contract(r), TXN_KEYS)
    out["examples/confirm-request.json"] = message("confirm", r, t["confirm"], on_select_contract(r), TXN_KEYS)
    out["examples/on-confirm-response.json"] = message("on_confirm", r, t["on_confirm"], active_contract(r, [row("2026-10-02T12:05:00Z", "QUEUED")]), SESSION_KEYS)
    out["examples/on-status-response-assigned.json"] = message("on_status", r, "2026-10-02T18:12:00Z", active_contract(r, RESERVATION_LEDGER_ASSIGNED), SESSION_KEYS)
    out["examples/on-status-response-settled.json"] = message("on_status", r, "2026-10-02T19:04:05Z", active_contract(r, RESERVATION_LEDGER_SETTLED, "COMPLETE", "CLOSED"), SESSION_KEYS)
    out["examples/cancel-request.json"] = message("cancel", r, "2026-10-02T17:30:00Z", active_contract(r, [row("2026-10-02T12:05:00Z", "QUEUED")]), SESSION_KEYS)
    out["examples/on-cancel-response.json"] = message("on_cancel", r, "2026-10-02T17:30:02Z", active_contract(r, RESERVATION_LEDGER_CANCELLED, "CANCELLED", "CLOSED"), SESSION_KEYS)

    too_soon = copy.deepcopy(message("select", r, "2026-10-02T17:20:00Z", select_contract(r), TXN_KEYS))
    too_soon["context"]["transactionId"] = "9c0d1e2f-3a4b-4c5d-8e6f-7a8b9c0d1e04"
    out["examples/select-request-reservation-too-soon.json"] = too_soon

    early = message("on_status", r, "2026-10-02T18:16:05Z", active_contract(r, RESERVATION_LEDGER_EARLY_NO_SHOW, "COMPLETE", "CLOSED"), SESSION_KEYS)
    early["context"]["transactionId"] = "4d5e6f7a-8b9c-4d0e-9f1a-2b3c4d5e6f05"
    out["examples/on-status-response-early-no-show.json"] = early

    tw = w["times"]
    out["examples/select-request-walk-in.json"] = message("select", w, tw["select"], select_contract(w), TXN_KEYS)
    out["examples/init-request-walk-in.json"] = message("init", w, tw["init"], on_select_contract(w), TXN_KEYS)
    out["examples/confirm-request-walk-in.json"] = message("confirm", w, tw["confirm"], on_select_contract(w), TXN_KEYS)
    out["examples/on-status-response-walk-in-settled.json"] = message("on_status", w, "2026-10-02T11:12:05Z", active_contract(w, WALK_IN_LEDGER_SETTLED, "COMPLETE", "CLOSED"), SESSION_KEYS)

    # Sandbox fixtures: the BPP app's answers to the reservation flow.
    for action, src in [("on_select", "on-select-response"), ("on_init", "on-init-response"), ("on_confirm", "on-confirm-response"), ("on_cancel", "on-cancel-response")]:
        out[f"responses/bpp/{action}.json"] = out[f"examples/{src}.json"]
    return out


def main():
    for rel, doc in build().items():
        path = UC_ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_format_payload(doc) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
