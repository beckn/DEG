#!/usr/bin/env python3
"""Add the EV charging use-case variants that the rc example set does not cover.

Reads the converted LTS examples (rc2lts.py output) and derives each variant from the
same flow (same transaction, contract, CPO, connector and offer), so every file is
consistent with the main path. Amounts are recomputed so each price breakup adds up.

Usage: variants.py <LTS examples dir>
"""
import copy
import json
import pathlib
import sys
import uuid

root = pathlib.Path(sys.argv[1])
PRICE_CTX = "https://schema.nfh.global/PriceSpecification/v2.1/context.jsonld"
PAY_CTX = "https://schema.nfh.global/Payment/v2.0/context.jsonld"
RATE = 45.0  # INR per kWh, offer-ccs2-60kw-kwh


def load(rel):
    return json.load(open(root / rel))


def save(rel, d):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print("wrote", rel)


def msg_id(rel):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "deg-ev-lts/" + rel))


def with_ctx(base, rel, action, ts, **extra):
    d = copy.deepcopy(base)
    d["context"].update({"action": action, "messageId": msg_id(rel), "timestamp": ts}, **extra)
    return d


def breakup(energy_kwh, extra=(), quote=False):
    """Price lines with the model the main flow uses (rc2lts.priced)."""
    base = RATE * energy_kwh
    lines = [("UNIT", base, f"Charging energy ({RATE:g} INR/kWh x {energy_kwh:g} kWh)"),
             ("SURCHARGE", base * 0.20, "Surge price (20% of energy cost)"),
             ("DISCOUNT", -base * 0.15, "Offer discount (15% of energy cost)"),
             ("FEE", 10.0, "Service fee")]
    if quote:
        lines.append(("FEE", RATE * 0.3, "Overcharge estimate (0.3 kWh, refunded if unused)"))
    lines += list(extra)
    lines.append(("FEE", base * 0.025, "Buyer finder fee (2.5% of energy cost)"))
    return [(t, round(v, 2), d) for t, v, d in lines]


def consideration(comps, status):
    total = round(sum(v for _, v, _ in comps), 2)
    return [{
        "id": "consideration-001",
        "status": {"code": status},
        "considerationAttributes": {
            "@context": PRICE_CTX, "@type": "PriceSpecification", "currency": "INR", "value": total,
            "components": [{"type": t, "value": v, "currency": "INR", "description": d} for t, v, d in comps],
        },
    }], total


def payment(sid, status, settle_status, amount, beneficiary, txn, paid_at, pid):
    return {
        "id": sid, "considerationId": "consideration-001", "status": settle_status,
        "settlementAttributes": {
            "@context": PAY_CTX, "@type": "Payment", "beckn:id": pid,
            "beckn:paymentStatus": status, "beckn:amount": {"currency": "INR", "value": amount},
            "beckn:txnRef": txn, "beckn:paidAt": paid_at, "beckn:beneficiary": beneficiary,
        },
    }


def balance(total, txn, when):
    """Settlement for the difference between what was paid and the final bill: a refund to
    the buyer, or (when the bill is higher) an amount the buyer still owes."""
    diff = round(PAID_AMOUNT - total, 2)
    if diff == 0:
        return None
    if diff > 0:
        return payment("settlement-002", "REFUNDED", "COMPLETE", diff, "BUYER", txn, when, "refund-001")
    return {"id": "settlement-002", "considerationId": "consideration-001", "status": "DRAFT",
            "settlementAttributes": {"@context": PAY_CTX, "@type": "Payment", "beckn:paymentStatus": "PENDING",
                                     "beckn:amount": {"currency": "INR", "value": -diff}, "beckn:beneficiary": "BPP"}}


def session(**fields):
    return {"@context": "https://schema.nfh.global/EvChargingSession/v2.0/context.jsonld",
            "@type": "ChargingSession", **fields}


def error(code, message, path, cause=None):
    e = {"code": code, "message": message, "details": {"path": path}}
    if cause:
        e["details"]["cause"] = cause
    return e


sel = load("03_select/ev-charging-select.json")
on_sel = load("04_on_select/ev-charging-on-select.json")
on_conf = load("08_00_on_confirm/ev-charging-on-confirm.json")
on_upd = load("10_on_update/ev-charging-session-on-update.json")
done = load("14_02_on_update/ev-charging-session-complete-on-update.json")
cancel = load("19_cancel/ev-charging-cancel-reserved-slot.json")
catalog = load("02_on_discover/ev-charging-discovery-catalog.json")
paid = on_conf["message"]["contract"]["settlements"][0]
PAID_AMOUNT = paid["settlementAttributes"]["beckn:amount"]["value"]
CID = on_conf["message"]["contract"]["id"]

# V0 confirm for the reservation flow where the consumer app collected the payment
rel = "07_confirm/ev-charging-bap-payment-confirm.json"
bap_init = load("06_on_init/ev-charging-bap-payment-on-init.json")
d = with_ctx(load("07_confirm/ev-charging-confirm.json"), rel, "confirm", "2025-01-27T10:04:00Z")
c = copy.deepcopy(bap_init["message"]["contract"])
st = c["settlements"][0]
st["status"] = "COMPLETE"
st["settlementAttributes"].update({"beckn:paymentStatus": "COMPLETED", "beckn:txnRef": "BAP-UPI-7781234567",
                                   "beckn:paidAt": "2025-01-27T10:03:40Z"})
d["message"] = {"contract": c}
save(rel, d)

# V1 on_select: requested slot overlaps an existing booking (async business error)
rel = "04_on_select/ev-charging-on-select-slot-unavailable.json"
d = with_ctx(on_sel, rel, "on_select", "2025-01-27T10:00:30Z")
d["message"]["contract"].pop("consideration", None)
d["error"] = error("BIZ_FULFILLMENT_UNAVAILABLE",
                   "Requested charging slot 2025-12-20 10:00-11:30 UTC overlaps an existing booking.",
                   "$.message.contract.contractAttributes.preferences")
save(rel, d)

# V2 on_select: quote carries an outstanding balance from an earlier session
rel = "04_on_select/ev-charging-on-select-outstanding-dues.json"
d = with_ctx(on_sel, rel, "on_select", "2025-01-27T10:00:30Z")
comps = breakup(2.5, quote=True) + [("FEE", 18.4, "Outstanding balance from an earlier session (overcharge, unpaid)")]
d["message"]["contract"]["consideration"], _ = consideration(comps, "QUOTED")
save(rel, d)

# V3 on_update: start-charging rejected, EVSE inoperative (error chain, NFH-008 style)
rel = "10_on_update/ev-charging-session-start-rejected-on-update.json"
d = with_ctx(on_conf, rel, "on_update", "2025-01-27T10:16:00Z")
perf = d["message"]["contract"]["performance"][0]
perf["status"] = {"code": "PENDING"}
perf["performanceAttributes"] = session(sessionStatus="PENDING", connectorStatus="UNAVAILABLE",
                                        connectorType="CCS2", maxPowerKW=50)
d["error"] = error("BIZ_FULFILLMENT_UNAVAILABLE", "Charging session could not be started at the requested EVSE.",
                   "$.message.contract.performance[0]",
                   {"code": "EVSE_INOPERATIVE",
                    "message": "OCPI 2.2: StartSession rejected, EVSE IN*ECO*BTM*01*CCS2*A status is INOPERATIVE."})
save(rel, d)

# V4 on_status (async): power cut mid-session, billed for energy delivered, balance refunded
rel = "13_on_status/ev-charging-session-undercharge-refund-on-status.json"
d = with_ctx(done, rel, "on_status", "2025-01-27T10:48:00Z")
c = d["message"]["contract"]
c["consideration"], total = consideration(breakup(1.2), "FINAL")
c["performance"][0]["status"] = {"code": "INTERRUPTED"}
c["performance"][0]["performanceAttributes"] = session(
    sessionStatus="INTERRUPTED", meteredEnergyKWh=1.2, meteredDurationMinutes=14,
    lastUpdated="2025-01-27T10:47:30Z", totalCost={"inclVat": total})
c["settlements"] = [x for x in (paid, balance(total, "RFND-TXN-123456789", "2025-01-27T10:48:00Z")) if x]
save(rel, d)

# V5 on_update: charger lost its CMS link and kept dispensing 0.3 kWh; the overcharge is
# billed against the pre-collected overcharge estimate, so nothing is refunded or owed
rel = "14_02_on_update/ev-charging-session-overcharge-on-update.json"
d = with_ctx(done, rel, "on_update", "2025-01-27T11:35:00Z")
c = d["message"]["contract"]
comps = breakup(2.5, [("FEE", 13.5, "Overcharge: 0.3 kWh delivered after the charger lost its CMS link")])
c["consideration"], total = consideration(comps, "FINAL")
c["performance"][0]["performanceAttributes"] = session(
    sessionStatus="COMPLETED", meteredEnergyKWh=2.8, meteredDurationMinutes=31,
    lastUpdated="2025-01-27T11:34:00Z", totalCost={"inclVat": total})
c["settlements"] = [x for x in (paid, balance(total, "RFND-TXN-123456790", "2025-01-27T11:35:00Z")) if x]
save(rel, d)

# V6 on_update: vehicle stopped drawing power early (battery full), billed for 2.0 kWh
rel = "14_02_on_update/ev-charging-session-undercharge-on-update.json"
d = with_ctx(done, rel, "on_update", "2025-01-27T11:20:00Z")
c = d["message"]["contract"]
c["consideration"], total = consideration(breakup(2.0), "FINAL")
c["performance"][0]["performanceAttributes"] = session(
    sessionStatus="COMPLETED", meteredEnergyKWh=2.0, meteredDurationMinutes=24,
    lastUpdated="2025-01-27T11:19:00Z", totalCost={"inclVat": total})
c["settlements"] = [x for x in (paid, balance(total, "RFND-TXN-123456791", "2025-01-27T11:20:00Z")) if x]
save(rel, d)

# V7 on_update: invoice ready after completion (Contract.descriptor.docs)
rel = "14_03_on_update/ev-charging-invoice-ready-on-update.json"
d = with_ctx(done, rel, "on_update", "2025-01-27T12:00:00Z")
d["message"]["contract"]["descriptor"] = {
    "name": "EV charging session order-ev-charging-001",
    "docs": [{"label": "Tax invoice INV-ECO-2025-000123", "mimeType": "application/pdf",
              "url": "https://example-bpp.com/invoices/order-ev-charging-001.pdf"}],
}
save(rel, d)

# V8 track / on_track: live session view handle (LTS /track)
commit = on_upd["message"]["contract"]["commitments"]
rel = "21_track/ev-charging-session-track.json"
d = with_ctx(on_upd, rel, "track", "2025-01-27T10:30:00Z")
# Tracking requires url and status even in the request (spec gap, see README):
# the CN sends the session's own deep link and the state it wants to follow.
d["message"] = {"tracking": {"contract": {"id": CID, "commitments": commit}, "status": "ACTIVE",
                             "url": "https://example-bap.com/sessions/order-ev-charging-001"}}
save(rel, d)
rel = "22_on_track/ev-charging-session-on-track.json"
d = with_ctx(on_upd, rel, "on_track", "2025-01-27T10:30:02Z")
d["message"] = {"tracking": {
    "contract": {"id": CID, "commitments": commit}, "status": "ACTIVE",
    "url": "https://track.bluechargenet-aggregator.io/session/SESSION-9876543210",
    "trackingAttributes": session(sessionStatus="ACTIVE", meteredEnergyKWh=1.1,
                                  lastUpdated="2025-01-27T10:30:00Z"),
}}
save(rel, d)

# V9 cancel preview (context.try=true) and the terms returned
rel = "19_cancel/ev-charging-cancel-preview.json"
d = with_ctx(cancel, rel, "cancel", "2025-01-27T09:40:00Z", **{"try": True})
d["message"]["contract"]["descriptor"] = {"code": "USER_CHANGED_PLANS", "shortDesc": "Plans changed"}
save(rel, d)
rel = "20_on_cancel/ev-charging-cancel-preview-on-cancel.json"
d = with_ctx(on_conf, rel, "on_cancel", "2025-01-27T09:40:02Z", **{"try": True})
c = d["message"]["contract"]
c["descriptor"] = {"code": "CANCELLATION_TERMS",
                   "shortDesc": "Free cancellation up to 30 minutes before the slot; 10% of the energy cost after that."}
c["consideration"], fee = consideration(
    [("FEE", 11.25, "Late cancellation fee (10% of energy cost, within 30 minutes of the slot)")], "QUOTED")
c.pop("performance", None)
c["settlements"] = [paid, {
    "id": "settlement-002", "considerationId": "consideration-001", "status": "DRAFT",
    "settlementAttributes": {"@context": PAY_CTX, "@type": "Payment", "beckn:paymentStatus": "PENDING",
                             "beckn:amount": {"currency": "INR", "value": round(PAID_AMOUNT - fee, 2)},
                             "beckn:beneficiary": "BUYER"}}]
save(rel, d)

# V10 on_cancel initiated by the CPO (unsolicited): charger fault, full refund
rel = "20_on_cancel/ev-charging-cpo-initiated-on-cancel.json"
d = with_ctx(on_conf, rel, "on_cancel", "2025-01-27T09:55:00Z")
c = d["message"]["contract"]
c["status"] = {"code": "CANCELLED"}
c["descriptor"] = {"code": "CPO_CHARGER_FAULT",
                   "shortDesc": "The reserved charger is out of service; the booking is cancelled with a full refund."}
for cm in c["commitments"]:
    cm["status"] = {"descriptor": {"code": "CLOSED"}}
c["consideration"][0]["status"] = {"code": "REFUNDED"}
c.pop("performance", None)
c["settlements"] = [paid, payment("settlement-002", "REFUNDED", "COMPLETE", PAID_AMOUNT, "BUYER",
                                  "RFND-TXN-123456792", "2025-01-27T09:55:00Z", "refund-001")]
save(rel, d)

# V11 support about a connector fault, and the resolved ticket
rel = "17_support/ev-charging-connector-fault-support.json"
d = with_ctx(load("17_support/ev-charging-session-support.json"), rel, "support", "2025-01-27T11:40:00Z")
d["message"]["support"]["descriptor"] = {
    "code": "CONNECTOR_FAULT", "name": "Connector not releasing",
    "shortDesc": "Charging stopped but the CCS2 connector is still locked to the vehicle."}
save(rel, d)
rel = "18_on_support/ev-charging-support-resolved-on-support.json"
d = with_ctx(load("18_on_support/ev-charging-session-on-support.json"), rel, "on_support", "2025-01-27T11:52:00Z")
s = d["message"]["support"]
s["descriptor"] = {"code": "RESOLVED", "name": "Ticket SUP-20250730-002 resolved",
                   "shortDesc": "Connector released remotely by the CPO at 11:51 UTC."}
s["channels"][0]["callbackStatus"] = "COMPLETED"
save(rel, d)

# V12 catalog/publish (CPO -> discovery service) and the acknowledgement
cat = catalog["message"]["catalogs"][0]
rel = "23_catalog_publish/ev-charging-catalog-publish.json"
d = {"context": {k: v for k, v in catalog["context"].items() if k not in ("bapId", "bapUri")},
     "message": {"catalogs": [cat]}}
d["context"].update({"action": "catalog/publish", "messageId": msg_id(rel), "timestamp": "2025-10-01T00:00:00Z",
                     "bppId": "example-bpp.com", "bppUri": "https://example-bpp.com/pilot/bpp/energy/v2"})
save(rel, d)
rel = "24_catalog_on_publish/ev-charging-catalog-on-publish.json"
d2 = copy.deepcopy(d)
d2["context"].update({"action": "catalog/on_publish", "messageId": msg_id(rel), "timestamp": "2025-10-01T00:00:05Z"})
d2["message"] = {"results": [{"catalogId": cat["id"], "status": "ACCEPTED",
                              "stats": {"itemCount": len(cat["resources"]), "providerCount": 1}}]}
save(rel, d2)
