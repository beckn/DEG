#!/usr/bin/env python3
"""
Beckn Postman Collection Generator

This script builds Postman collections from the example JSON flows in this repo for a
given devkit (e.g., ev-charging) and role (BAP or BPP). It wires in context macros so
requests route correctly within the devkit testnets, and can optionally validate the
resulting collection against Beckn schemas.

WHAT IT DOES
------------
1) Discovers example JSON files under a devkit-specific examples directory
2) Builds Postman items for each API flow, adding environment macros for BAP/BPP IDs and URIs
3) Writes a Postman collection JSON to the requested output directory
4) Optionally validates the generated collection using the local `validate_schema.py`

KEY FUNCTIONS
-------------
- `generate_collection(...)`: Core builder; converts example flows to Postman items
- `build_item(...)`: Creates a Postman item with request, headers, and body
- `attach_env_macros(...)`: Injects {{bap_id}}, {{bap_uri}}, {{bpp_id}}, {{bpp_uri}}
  placeholders so the same collection works across environments
- `main()`: CLI entry point (parses args, resolves paths, runs generation, optional validation)

CLI USAGE
---------
python3 scripts/generate_postman_collection.py \\
  --devkit ev-charging \\
  --role BAP \\
  --output-dir devkits/ev-charging/postman \\
  --examples examples/ev-charging/v2 \\
  --name ev-charging.BAP-DEG \\
  --description \"EV Charging BAP flows\" \\
  --validate

Arguments:
- --devkit        Devkit key (e.g., ev-charging)
- --role          Role in the flows (BAP or BPP)
- --output-dir    Where to write the Postman collection
- --examples      Root path to example JSONs (defaults from devkit config)
- --name          Collection name (default: <devkit>.<role>-DEG)
- --description   Collection description (optional)
- --validate      Run schema validation on the generated collection using validate_schema.py

OUTPUT
------
Writes a Postman collection JSON with environment macros for IDs/URIs, suitable for
importing into Postman or running via newman with environment files.
"""

import copy
import fnmatch
import json
import os
import re
import uuid
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    import yaml as _yaml
except ImportError:
    _yaml = None

# Import validation functions from validate_schema
try:
    # Try importing as module (if scripts directory is in path)
    from validate_schema import get_schema_store, process_file
except ImportError:
    # If running as a script, import from same directory
    import importlib.util
    validate_schema_path = Path(__file__).parent / "validate_schema.py"
    if validate_schema_path.exists():
        spec = importlib.util.spec_from_file_location("validate_schema", validate_schema_path)
        validate_schema = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validate_schema)
        get_schema_store = validate_schema.get_schema_store
        process_file = validate_schema.process_file
    else:
        get_schema_store = None
        process_file = None


# Configuration for different devkits
DEVKIT_CONFIGS = {
    "ev-charging": {
        "domain": "beckn.one:deg:ev-charging:2.0.0",
        "bap_id": "ev-charging.sandbox1.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "ev-charging.sandbox2.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/ev-charging/uc1-ev-charging/examples",
        "structure": "folders"  # Folder-based structure
    },
    "ev-charging-uc2-ev-charging": {
        # Settlement-first EV charging on Beckn v2 LTS (self-contained stack
        # under devkits/ev-charging/uc2-ev-charging/install).
        "endpoint_overrides": {"publish": "catalog/publish"},
        "domain": "nfh.global/testnet-deg",
        "bap_id": "bap.example.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "bpp.example.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "transaction_id": "7f1c2b9e-4d3a-4e8f-9b61-2a5c8d0e1f01",
        "examples_path": "devkits/ev-charging/uc2-ev-charging/examples",
        "structure": "flat"
    },
    "p2p-trading": {
        "domain": "beckn.one:deg:p2p-trading:2.0.0",
        "bap_id": "p2p-trading-sandbox1.com",
        "bap_uri": "http://onix-bap:8081/bap/receiver",
        "bpp_id": "p2p-trading-sandbox2.com",
        "bpp_uri": "http://onix-bpp:8082/bpp/receiver",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "examples/p2p-trading/v2",
        # "output_path": "devkits/p2p-trading/postman",
        "structure": "flat"  # Flat file structure
    },
    "p2p-enrollment": {
        "domain": "beckn.one:deg:p2p-enrollment:2.0.0",
        "bap_id": "p2p-enrollment-sandbox1.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "p2p-enrollment-sandbox2.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/p2p-enrollment/uc1-p2p-enrollment/examples",
        "structure": "flat"  # Flat file structure (like p2p-trading)
    },
    "p2p-trading-interdiscom": {
        "domain": "beckn.one:deg:p2p-trading-interdiscom:2.0.0",
        "bap_id": "p2p-trading-sandbox1.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "p2p-trading-sandbox2.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/p2p-trading-interdiscom/uc1-p2p-trading-interdiscom/examples",
        "structure": "flat"  # Flat file structure (like p2p-trading)
    },
    "demand-flex": {
        # Routing configs declare the Beckn v2 compound catalog endpoint.
        "endpoint_overrides": {"publish": "catalog/publish"},
        # {{domain}} substitutes context.networkId (and publishDirectives
        # visibleTo[0]) in v2 LTS payloads — it must hold the network id,
        # not the legacy beckn domain string.
        "domain": "nfh.global/testnet-deg",
        "bap_id": "bap.example.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "bpp.example.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/demand-flex/uc1-bdr-w-baselining/examples",
        "structure": "flat"
    },
    "demand-flex-uc2-bid-curve-pac": {
        # Routing configs declare the Beckn v2 compound catalog endpoint.
        "endpoint_overrides": {"publish": "catalog/publish"},
        "domain": "nfh.global/testnet-deg",
        "bap_id": "bap.example.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "bpp.example.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "transaction_id": "c2d3e4f5-a6b7-8901-abcd-ef5678901234",
        "examples_path": "devkits/demand-flex/uc2-bid-curve-pac/examples",
        "structure": "flat"
    },
    "p2p-trading-ies-wave1": {
        "domain": "beckn.one:deg:p2p-trading-interdiscom:2.0.0",
        "bap_id": "p2p-trading-sandbox1.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "p2p-trading-sandbox2.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/p2p-trading-ies-wave1/uc1/examples",
        "structure": "flat"
    },
    "p2p-trading-ies-wave2": {
        # Routing configs declare the Beckn v2 compound catalog endpoint.
        "endpoint_overrides": {"publish": "catalog/publish"},
        # Default trading network for the devkit. nfh.global/testnet-deg is
        # still recognized everywhere (configs, policy, sandbox fixture
        # mounts) — override the {{domain}} variable to use it.
        "domain": "indiaenergystack.in/test-ies-p2p-trading-network",
        # Per-node Beckn hostnames matching discomIds (resolve via Caddy
        # host-routing + Docker network aliases on beckn-router). Each
        # participant lives on its own host; standard Beckn paths (/bap/receiver,
        # /bpp/receiver, etc.) live under each. SubscriberIds name the entity
        # (buyerapp/sellerapp), not the protocol role.
        "bap_id": "buyerapp.example.com",
        "bap_host_root": "http://buyerapp.example.com:9000",
        "bpp_id": "sellerapp.example.com",
        "bpp_host_root": "http://sellerapp.example.com:9000",
        # Platform identities under their business names — emitted for the
        # ledger/discom collections too, so contract-body participantId /
        # platformUrl substitutions resolve in every collection (BUYER/SELLER
        # already get these via var_names renaming of bap_/bpp_).
        "buyerplatform_id": "buyerapp.example.com",
        "buyerplatform_host_root": "http://buyerapp.example.com:9000",
        "sellerplatform_id": "sellerapp.example.com",
        "sellerplatform_host_root": "http://sellerapp.example.com:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        # Endpoint sellerapp exposes when it initiates a sub-tx (seller-initiated
        # status to buyer or to seller-discom). New in this devkit; mirrors
        # buyerapp's /bap/caller but on port 8082.
        "seller_bap_caller_url": "http://localhost:8082/bap/caller",
        # Ledger TSP base URLs (ledgerUri on DiscomLedgerProvider). Match the
        # local example.com hosts used by uc1 examples / docker-compose; override
        # the Postman variable to point at a shared IES ledger if needed.
        "ledger_host_buyer": "https://ies-p2p-energy-ledger.beckn.io",
        "ledger_host_seller": "https://ies-p2p-energy-ledger.beckn.io",
        "examples_path": "devkits/p2p-trading-ies-wave2/uc1/examples",
        # Source dirs for the discom-ledger TSP collections. The on_status.json
        # response fixtures here ARE the canonical outbound on_status payloads
        # the ledger sends back to platforms.
        "buyerdiscomledger_examples_path": "devkits/p2p-trading-ies-wave2/responses/buyerdiscom",
        "sellerdiscomledger_examples_path": "devkits/p2p-trading-ies-wave2/responses/sellerdiscom",
        # Adapter URLs for the discom-ledger /bpp/caller endpoints (the ledger
        # signs and routes the on_status to context.bapUri). Default host-side
        # ports per install/docker-compose.yml: buyerdiscom=8084, sellerdiscom=8083.
        "buyer_ledger_bpp_caller_url": "http://localhost:8084/bpp/caller",
        "seller_ledger_bpp_caller_url": "http://localhost:8083/bpp/caller",
        # /bap/caller URLs for ledger-initiated status requests to discom utilities.
        # Requires a bapTxnCaller module to be added to each ledger's onix config.
        "buyer_ledger_bap_caller_url": "http://localhost:8084/bap/caller",
        "seller_ledger_bap_caller_url": "http://localhost:8083/bap/caller",
        # Sellerdiscom *actor* (the utility itself, distinct from the ledger
        # TSP). New Beckn-native channel for pushing meter actuals as
        # on_status — DatasetItem-wrapped BecknTimeSeries — to the ledger.
        # Source fixture (sellerdiscom-on-status*.json) lives in the
        # shared examples dir; the SELLERDISCOM filter discriminates it.
        "sellerdiscom_host_root": "http://sellerdiscom.example.com:9000",
        "sellerdiscom_bpp_caller_url": "http://localhost:8086/bpp/caller",
        # Buyerdiscom actor (the buyer's utility), symmetric to sellerdiscom.
        # Pushes meter actuals as on_status to buyer-discom-ledger /bap/receiver.
        "buyerdiscom_host_root": "http://buyerdiscom.example.com:9000",
        "buyerdiscom_bpp_caller_url": "http://localhost:8085/bpp/caller",
        # Platform URLs for the discom Beckn platforms (distinct from the ledger
        # TSP URLs). Used for trade allocation requests; emitted as dedicated
        # Postman variables so testers can override them independently.
        # These map to DiscomLedgerProvider.discomUri in the payload.
        "buyer_discom_host_url": "http://buyer-discom.example.com:9000",
        "seller_discom_host_url": "http://seller-discom.example.com:9000",
        # Discom Beckn discomIds (DiscomLedgerProvider.discomId) —
        # routing/signing identity of the discom platform, distinct from the
        # UPADHI short code used as participants[].id / roles[].participantId.
        "buyer_discom_subscriber_id": "buyer-discom.example.com",
        "seller_discom_subscriber_id": "seller-discom.example.com",
        # Ledger TSP subscriber IDs (DiscomLedgerProvider.ledgerId). Emitted as
        # Postman variables in all wave2 collections. seller_discom_ledger_id is
        # also used in substitutions.yaml for context.bppId in
        # seller-initiated-status-to-seller-discom flows.
        "ledger_buyer_discom_id": "ies-p2p-energy-ledger.beckn.io",
        "ledger_seller_discom_id": "ies-p2p-energy-ledger.beckn.io",
        "transaction_id": "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2026",
        "seller_discom_ledger_id": "seller-discom-ledger.example.com",
        "usecase": "uc1",
        "structure": "flat",
        # Rename the generic bap/bpp_* Postman variables to domain-specific names
        # so testers immediately understand what each variable represents, and so
        # seller-initiated requests read naturally (e.g. "bapId": {{sellerplatform_id}}
        # instead of the confusing "bapId": {{bpp_id}}).
        # Only applied to BAP/BPP (buyer/seller) collections; ledger/discom
        # collections keep the generic names to avoid ambiguity.
        "var_names": {
            "bap_id":         "buyerplatform_id",
            "bpp_id":         "sellerplatform_id",
            "bap_host_root":  "buyerplatform_host_root",
            "bpp_host_root":  "sellerplatform_host_root",
        },
        # Legacy participant-attribute map (used only when substitutions.yaml is
        # absent). Keys are role names from the older role-bearing participants[]
        # shape; wave2 now uses role-less participants[] + substitutions.yaml.
        "participant_attr_vars": {
            "buyer":        {"platformUrl": "buyerplatform_host_root"},
            "seller":       {"platformUrl": "sellerplatform_host_root"},
            "buyerDiscom":  {"ledgerUri": "ledger_host_buyer",  "discomUri": "buyer_discom_host_url"},
            "sellerDiscom": {"ledgerUri": "ledger_host_seller", "discomUri": "seller_discom_host_url"},
        },
    },
    "data-exchange-uc1-meter-data": {
        "domain": "nfh.global/testnet-deg",
        "bap_id": "bap.example.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "bpp.example.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/data-exchange/uc1-meter-data/examples",
        "structure": "flat"
    },
    "data-exchange-uc2-regulatory-data": {
        "domain": "nfh.global/testnet-deg",
        "bap_id": "bap.example.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "bpp.example.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/data-exchange/uc2-regulatory-data/examples",
        "structure": "flat"
    },
    "data-exchange-uc3-tariff-policy": {
        "domain": "nfh.global/testnet-deg",
        "bap_id": "bap.example.com",
        "bap_host_root": "http://beckn-router:9000",
        "bpp_id": "bpp.example.com",
        "bpp_host_root": "http://beckn-router:9000",
        "bap_caller_url": "http://localhost:8081/bap/caller",
        "bpp_caller_url": "http://localhost:8082/bpp/caller",
        "examples_path": "devkits/data-exchange/uc3-tariff-policy/examples",
        "structure": "flat"
    }
}

# Public-role -> canonical-role aliases. The CLI accepts both BAP/BPP/UtilityBPP
# (legacy transport-role names) and business-role names (BUYER, SELLER, …)
# plus the new ledger roles. Aliases let one filter/action table cover multiple
# devkit semantics: e.g. demand-flex's "BUYER" (utility issuing
# DemandFlexBuyOffers) and p2p's "BUYER" (consumer buying energy) both map to
# BAP plumbing; only the output filename uses the public name.
#
# BUYERDISCOMLEDGER / SELLERDISCOMLEDGER are NOT aliases — they're new
# canonical roles for discom-ledger TSPs. They source files from a separate
# examples path (the response fixtures dir) and emit on_status callbacks only.
ROLE_ALIAS = {
    # Legacy transport roles (identity)
    "BAP": "BAP",
    "BPP": "BPP",
    "UtilityBPP": "UtilityBPP",
    # Business-role names for v2 LTS devkits
    "BUYER": "BAP",
    "SELLER": "BPP",
    # Discom-ledger TSP roles (new canonical)
    "BUYERDISCOMLEDGER": "BUYERDISCOMLEDGER",
    "SELLERDISCOMLEDGER": "SELLERDISCOMLEDGER",
    # Sellerdiscom actor — seller-side discom utility pushing meter actuals
    # as on_status to sellerdiscomledger /bap/receiver.
    "SELLERDISCOM": "SELLERDISCOM",
    # Buyerdiscom actor — buyer-side discom utility pushing meter actuals
    # as on_status to buyerdiscomledger /bap/receiver.
    "BUYERDISCOM": "BUYERDISCOM",
}


def canonical_role(public_role: str) -> str:
    """Translate the CLI-facing role name to the canonical role used by filters,
    action tables, and adapter URL lookup. Raises ValueError on unknown roles."""
    if public_role not in ROLE_ALIAS:
        raise ValueError(f"Unknown role: {public_role!r}; expected one of {sorted(ROLE_ALIAS.keys())}")
    return ROLE_ALIAS[public_role]


# Role-based file name filters (regex patterns). Keyed by canonical role.
ROLE_FILTERS = {
    "BAP": [
        r".*-request.*\.json$",  # P2P trading/enrollment: *-request*.json (includes suffixes like -otp, -oauth2)
        r"^\d+_(discover|select|init|confirm|status|update|track|rating|support|cancel)\.json$",  # EV charging: numbered folders
        r"^(discover|select|init|confirm|status|update|track|rating|support|cancel).*\.json$",  # General pattern
    ],
    "BPP": [
        r"^(?!cascaded-).*-response.*\.json$",  # P2P trading/enrollment: *-response*.json (excludes cascaded-)
        r"^\d+_on_(discover|select|init|confirm|update|track|status|rating|support|cancel).*\.json$",  # EV charging: on_* folders
        r"^on[-_](discover|select|init|confirm|update|track|status|rating|support|cancel).*\.json$",  # General pattern (on- or on_)
        r"^publish-.*\.json$",  # BPP-initiated publish action to CDS
        # Seller-initiated requests where the seller (a BPP in the original
        # trade) plays BAP-caller for a sub-transaction it initiates: e.g.
        # asking the buyer about buyer-discom allocation status, or asking
        # its own discom ledger about its allocation. These files end up in
        # the SELLER collection routed to {{seller_bap_caller_url}}.
        r"^seller-initiated-.*\.json$",
    ],
    "UtilityBPP": [
        r"^cascaded-.*\.json$"  # Cascaded requests/responses
    ],
    # Discom-ledger TSP: outbound on_status emissions only (per design — the
    # collection lets a tester directly fire the ledger's on_status callback
    # via the ledger's /bpp/caller endpoint, bypassing the sandbox).
    "BUYERDISCOMLEDGER": [
        r"^on_status.*\.json$",
        r"^on-status.*\.json$",
        r"^status-request.*\.json$",
    ],
    "SELLERDISCOMLEDGER": [
        r"^on_status.*\.json$",
        r"^on-status.*\.json$",
        r"^status-request.*\.json$",
    ],
    # Sellerdiscom actor: pushes meter actuals as on_status via /bpp/caller.
    # Source fixture is named distinctly so it doesn't collide with the
    # SELLER (BPP) collection's on_status callbacks.
    "SELLERDISCOM": [
        r"^sellerdiscom-on[-_]status.*\.json$",
    ],
    # Buyerdiscom actor: symmetric to SELLERDISCOM; pushes meter actuals
    # as on_status from the buyer-side discom utility to buyerdiscomledger.
    "BUYERDISCOM": [
        r"^buyerdiscom-on[-_]status.*\.json$",
    ],
}

# All BAP-initiated actions (including status)
BAP_ACTIONS = {
    "discover": "discover",
    "select": "select",
    "init": "init",
    "confirm": "confirm",
    "status": "status",
    "update": "update",
    "track": "track",
    "rating": "rating",
    "support": "support",
    "cancel": "cancel",
}

# BPP-initiated actions (not callbacks, but BPP initiating requests to CDS, etc.)
BPP_INITIATED_ACTIONS = {
    "publish": "publish",
}

# BPP response actions
BPP_ACTIONS = {
    "on_discover": "on_discover",
    "on_select": "on_select",
    "on_init": "on_init",
    "on_confirm": "on_confirm",
    "on_status": "on_status",
    "on_update": "on_update",
    "on_track": "on_track",
    "on_rating": "on_rating",
    "on_support": "on_support",
    "on_cancel": "on_cancel",
}

# Pre-request script for ISO timestamp generation
PRE_REQUEST_SCRIPT = """// Pure JS pre-request script to replace moment()
// 1) ISO 8601 timestamp without needing moment
const isoTimestamp = new Date().toISOString();
pm.collectionVariables.set('iso_date', isoTimestamp);
"""


# Compact-yet-readable JSON formatting.
#
# `_format_payload` renders an object/array on ONE line whenever its compact
# form fits within `_MAX_INLINE` characters, so small structures — descriptor,
# status, quantity, eventWindow, policy, … — stay compact instead of sprawling
# across many lines, while keeping lines short enough to avoid horizontal
# scrolling. Larger structures (schemaContext, commitments, resources, inputs,
# meters, performance, offers, catalogs) exceed the budget and expand with
# 2-space indentation.
#
# Arrays under `_FORCE_ELEMENT_KEYS` get a stronger guarantee: when the array
# is too big to inline whole, each element is still emitted on its own single
# line. This keeps every TimeSeries `intervals[i]` (id + payloads) and every
# payloadDescriptor / reportDescriptor / role / participant on one row even
# when an individual element would otherwise wrap.
_MAX_INLINE = 200
_FORCE_ELEMENT_KEYS = {
    "intervals",
    "payloadDescriptors",
    "reportDescriptors",
    "vendorDevices",
    "roles",
    "participants",
    "revenueFlows",
    "ledger",
}


def _compact(node: Any) -> str:
    return json.dumps(node, separators=(", ", ": "), ensure_ascii=False)


def _format_payload(doc: Any, level: int = 0, force_elements: bool = False) -> str:
    """Pretty-print JSON, collapsing any object/array that fits on one line.

    A node renders inline when its compact form is <= `_MAX_INLINE` chars.
    Otherwise it expands with 2-space indentation and its children are
    formatted recursively. When `force_elements` is set (an array under a key
    in `_FORCE_ELEMENT_KEYS` that was too big to inline whole), each element is
    emitted compact on its own line.
    """
    compact = _compact(doc)
    if len(compact) <= _MAX_INLINE:
        return compact

    pad = "  " * level
    inner = "  " * (level + 1)

    if isinstance(doc, dict):
        items = list(doc.items())
        lines = []
        for i, (key, value) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            force = isinstance(value, list) and key in _FORCE_ELEMENT_KEYS
            rendered = _format_payload(value, level + 1, force)
            lines.append(f"{inner}{json.dumps(key, ensure_ascii=False)}: {rendered}{comma}")
        return "{\n" + "\n".join(lines) + f"\n{pad}}}"

    if isinstance(doc, list):
        lines = []
        for i, value in enumerate(doc):
            comma = "," if i < len(doc) - 1 else ""
            rendered = _compact(value) if force_elements else _format_payload(value, level + 1)
            lines.append(f"{inner}{rendered}{comma}")
        return "[\n" + "\n".join(lines) + f"\n{pad}]"

    return compact


def matches_role_filter(filename: str, role: str) -> bool:
    """
    Check if filename matches role-based filter patterns.
    
    Args:
        filename: Name of the file
        role: Role (BAP, BPP, or UtilityBPP)
    
    Returns:
        True if filename matches role filters
    """
    if role not in ROLE_FILTERS:
        return False
    
    for pattern in ROLE_FILTERS[role]:
        if re.match(pattern, filename, re.IGNORECASE):
            return True
    return False


def extract_action_from_filename(filename: str, role: str) -> Optional[str]:
    """
    Extract action name from filename based on role.
    
    Examples:
        "discover-request.json" (BAP) -> "discover"
        "discover-response.json" (BPP) -> "on_discover"
        "cascaded-init-request.json" (UtilityBPP) -> "init"
        "init-request-otp.json" (BAP) -> "init"
        "on-init-response-oauth2.json" (BPP) -> "on_init"
    """
    # Remove .json extension
    name = filename.replace('.json', '')
    
    # Handle P2P trading/enrollment flat structure - strict role-based matching
    if role == "BAP":
        # BAP only matches *-request*.json (not *-response*.json)
        # Pattern: action-request or action-request-suffix
        if '-request' in name and '-response' not in name:
            # Extract action from before -request
            match = re.match(r'^(cascaded-)?([a-z]+)-request', name, re.IGNORECASE)
            if match:
                is_cascaded = match.group(1) is not None
                action = match.group(2)
                if action in BAP_ACTIONS:
                    return action
    
    elif role == "BPP":
        # Seller-initiated request fixtures: action is encoded after the
        # seller-initiated-<action>- prefix. Routed to {{seller_bap_caller_url}}
        # later in the pipeline; treated as a regular BAP-side request action.
        if name.startswith('seller-initiated-'):
            match = re.match(r'^seller-initiated-([a-z]+)-', name, re.IGNORECASE)
            if match:
                action = match.group(1).lower()
                if action in BAP_ACTIONS:
                    return action

        # BPP matches *-response*.json (not *-request*.json) AND publish-*.json
        # AND *-request*.json whose action is in BPP_INITIATED_ACTIONS (e.g. status-request.json)
        # Patterns: action-response, on-action-response, action-response-suffix, publish-*

        # First check for BPP-initiated actions (like publish-catalog.json)
        if name.startswith('publish-'):
            match = re.match(r'^(publish)-', name, re.IGNORECASE)
            if match:
                action = match.group(1).lower()
                if action in BPP_INITIATED_ACTIONS:
                    return action

        # Check for request files whose action is in BPP_INITIATED_ACTIONS (e.g. status-request.json)
        if '-request' in name and '-response' not in name:
            match = re.match(r'^([a-z]+)-request', name, re.IGNORECASE)
            if match:
                action = match.group(1).lower()
                if action in BPP_INITIATED_ACTIONS:
                    return action

        if '-response' in name and '-request' not in name:
            # First try: on-action-response pattern (e.g., on-init-response-oauth2)
            match = re.match(r'^(cascaded-)?(on[-_])?([a-z]+)-response', name, re.IGNORECASE)
            if match:
                is_cascaded = match.group(1) is not None
                has_on_prefix = match.group(2) is not None
                action = match.group(3)

                if has_on_prefix:
                    # Already has on_ prefix (e.g., on-init-response -> on_init)
                    bpp_action = f"on_{action}"
                    if bpp_action in BPP_ACTIONS:
                        return bpp_action
                else:
                    # No on_ prefix, convert to BPP action (e.g., discover-response -> on_discover)
                    if action in BAP_ACTIONS:
                        return f"on_{action}"
    
    elif role == "UtilityBPP":
        # UtilityBPP matches cascaded-*-request*.json
        if name.startswith('cascaded-') and '-request' in name:
            match = re.match(r'^cascaded-([a-z]+)-request', name, re.IGNORECASE)
            if match:
                action = match.group(1)
                if action in BAP_ACTIONS:
                    return action

    elif role in ("BUYERDISCOMLEDGER", "SELLERDISCOMLEDGER"):
        if re.match(r'^on[-_]status', name, re.IGNORECASE):
            return "on_status"
        # Ledger-initiated status request to the discom utility (ledger as BAP).
        if re.match(r'^status-request', name, re.IGNORECASE):
            return "status"

    elif role == "SELLERDISCOM":
        # Sellerdiscom actor collection: outbound on_status push of
        # DatasetItem-wrapped meter actuals. File prefix
        # `sellerdiscom-on-status` discriminates the actor's push
        # fixture from any other on_status emitter sharing the examples dir.
        if re.match(r'^sellerdiscom-on[-_]status', name, re.IGNORECASE):
            return "on_status"

    elif role == "BUYERDISCOM":
        # Buyerdiscom actor collection: symmetric to SELLERDISCOM.
        if re.match(r'^buyerdiscom-on[-_]status', name, re.IGNORECASE):
            return "on_status"

    return None


def extract_action_from_folder(folder_name: str, role: str) -> Optional[str]:
    """
    Extract action name from folder name (for folder-based structure).
    
    Examples:
        "01_discover" (BAP) -> "discover"
        "02_on_discover" (BPP) -> "on_discover"
        "08_02_on_status" (BPP) -> "on_status"
        "03_select" (BAP) -> "select"
    """
    # Remove leading numbers and underscores
    # Handles both: \d+_action and \d+_\d+_action patterns
    match = re.match(r'^\d+(?:_\d+)?_(.+)$', folder_name)
    if match:
        action = match.group(1)
        
        if role == "BAP":
            # BAP uses regular actions
            if action in BAP_ACTIONS:
                return action
        elif role == "BPP":
            # BPP uses on_* actions
            if action in BPP_ACTIONS:
                return action
        elif role == "UtilityBPP":
            # UtilityBPP uses cascaded actions (same as BAP actions)
            if action in BAP_ACTIONS:
                return action
    
    return None


def get_request_name(filename: str) -> str:
    """
    Use filename directly as request name (remove .json extension).
    
    Examples:
        "discovery-along-route.json" -> "discovery-along-route"
        "time-based-ev-charging-slot-select.json" -> "time-based-ev-charging-slot-select"
        "discover-request.json" -> "discover-request"
    """
    return filename.replace('.json', '')


def load_example_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load and parse JSON example file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if not isinstance(data, dict):
            print(f"  Warning: {filepath.name} is not a JSON object, skipping")
            return None
        
        if "context" not in data or "message" not in data:
            print(f"  Warning: {filepath.name} missing 'context' or 'message', skipping")
            return None
        
        return data
    except json.JSONDecodeError as e:
        print(f"  Error: {filepath.name} is not valid JSON: {e}, skipping")
        return None
    except Exception as e:
        print(f"  Error reading {filepath.name}: {e}, skipping")
        return None


# ---------------------------------------------------------------------------
# Declarative substitution engine — reads substitutions.yaml if present in the
# collection output directory and applies path-based replacements instead of
# the role-inference logic in replace_context_macros / replace_participant_attr_macros.
# ---------------------------------------------------------------------------

def _load_substitutions(yaml_path: Path) -> Optional[Dict]:
    """Load substitutions.yaml. Returns None if the file doesn't exist or yaml unavailable."""
    if not yaml_path.exists():
        return None
    if _yaml is None:
        print(f"  Warning: pyyaml not installed; substitutions.yaml ignored ({yaml_path})")
        return None
    with yaml_path.open() as f:
        return _yaml.safe_load(f)


def _parse_path(path_str: str) -> List[tuple]:
    """
    Parse a dot-notation path with optional array filters or positional
    indices into segments.

    Dots *inside* bracket filters are preserved so domain-valued ids work:
      participants[id=buyerapp.example.com].participantAttributes.platformUrl

    'context.bapId'
      → [('key','context'), ('key','bapId')]

    'message.publishDirectives[0].visibleTo[0]'
      → [('key','message'), ('key','publishDirectives'), ('index',0),
         ('key','visibleTo'), ('index',0)]

    'message.contract.participants[role=buyer].participantAttributes.platformUri'
      → [('key','message'), ('key','contract'),
         ('key','participants'), ('filter','role','buyer'),
         ('key','participantAttributes'), ('key','platformUri')]

    'message.contract.participants[id=buyerapp.example.com].id'
      → [('key','message'), ('key','contract'),
         ('key','participants'), ('filter','id','buyerapp.example.com'),
         ('key','id')]
    """
    segments: List[tuple] = []
    i = 0
    n = len(path_str)
    while i < n:
        if path_str[i] == ".":
            i += 1
            continue
        if path_str[i] == "[":
            end = path_str.find("]", i)
            if end < 0:
                raise ValueError(f"Unclosed '[' in path {path_str!r}")
            inner = path_str[i + 1 : end].strip()
            if inner.isdigit() or (inner.startswith("-") and inner[1:].isdigit()):
                segments.append(("index", int(inner)))
            else:
                if "=" not in inner:
                    raise ValueError(
                        f"Array filter in path {path_str!r} must be index or field=value, got [{inner}]"
                    )
                field, value = inner.split("=", 1)
                segments.append(("filter", field.strip(), value.strip()))
            i = end + 1
            continue
        # Read a key token up to the next '.' or '['
        j = i
        while j < n and path_str[j] not in ".[":
            j += 1
        key = path_str[i:j]
        if not key:
            raise ValueError(f"Empty path segment in {path_str!r} at index {i}")
        segments.append(("key", key))
        i = j
    return segments


def _navigate_to_parent(obj: Any, segments: List[tuple], path_str: str, filename: str):
    """
    Walk obj following all but the last segment.
    Returns (parent_container, final_key_or_filter_or_index) so the caller can
    set a value. The final element is either a string (dict key) or an int
    (list index). Raises ValueError with a diagnostic message if any step fails.
    """
    current = obj
    for seg in segments[:-1]:
        kind = seg[0]
        if kind == "key":
            key = seg[1]
            if not isinstance(current, dict) or key not in current:
                raise ValueError(
                    f"{filename!r}: path {path_str!r}: key {key!r} not found"
                )
            current = current[key]
        elif kind == "index":
            idx = seg[1]
            if not isinstance(current, list):
                raise ValueError(
                    f"{filename!r}: path {path_str!r}: expected list for index [{idx}]"
                )
            if idx >= len(current) or idx < -len(current):
                raise ValueError(
                    f"{filename!r}: path {path_str!r}: index {idx} out of range (len={len(current)})"
                )
            current = current[idx]
        elif kind == "filter":
            _, field, value = seg
            if not isinstance(current, list):
                raise ValueError(
                    f"{filename!r}: path {path_str!r}: expected list for filter [{field}={value}]"
                )
            match = next(
                (item for item in current if isinstance(item, dict) and item.get(field) == value),
                None,
            )
            if match is None:
                raise ValueError(
                    f"{filename!r}: path {path_str!r}: no array item with {field}={value!r}"
                )
            current = match

    last = segments[-1]
    if last[0] == "key":
        return current, last[1]
    if last[0] == "index":
        return current, last[1]
    raise ValueError(
        f"{filename!r}: path {path_str!r}: path must end with a key or index, not an array filter"
    )


def _apply_substitutions(
    data: Dict[str, Any],
    filename: str,
    role: str,
    substitutions: Dict,
) -> Dict[str, Any]:
    """
    Apply declarative substitutions from substitutions.yaml to a single payload.

    Rules in `common` are applied first; role-specific rules follow.
    Within each list, later patterns that match the same file override earlier ones
    for the same path (last-writer-wins per path key).

    Each rule entry:
        - match: glob pattern or list of patterns (matched against filename basename)
        - paths: dict mapping path_str → {var, suffix?, required?}
    """
    data = copy.deepcopy(data)

    all_patterns: List[Dict] = list(substitutions.get("common", []))
    all_patterns.extend(substitutions.get("roles", {}).get(role, []))

    # Accumulate effective rules (path → rule), later patterns win
    effective: Dict[str, Dict] = {}
    for entry in all_patterns:
        raw_match = entry.get("match", "*.json")
        patterns = [raw_match] if isinstance(raw_match, str) else list(raw_match)
        if any(fnmatch.fnmatch(filename, p) for p in patterns):
            for path_str, rule in entry.get("paths", {}).items():
                effective[path_str] = rule

    for path_str, rule in effective.items():
        var = rule.get("var", "")
        suffix = rule.get("suffix", "")
        required = rule.get("required", True)
        new_value = f"{{{{{var}}}}}{suffix}"

        segments = _parse_path(path_str)
        try:
            container, key = _navigate_to_parent(data, segments, path_str, filename)
            if isinstance(key, int):
                if not isinstance(container, list):
                    raise ValueError(
                        f"{filename!r}: path {path_str!r}: final segment is an index but container is not a list"
                    )
                if key >= len(container) or key < -len(container):
                    raise ValueError(
                        f"{filename!r}: path {path_str!r}: final index {key} out of range (len={len(container)})"
                    )
                container[key] = new_value
            else:
                if not isinstance(container, dict) or key not in container:
                    raise ValueError(
                        f"{filename!r}: path {path_str!r}: final key {key!r} not found"
                    )
                container[key] = new_value
        except ValueError as exc:
            if required:
                raise
            # optional path — skip silently

    return data


def replace_context_macros(
    data: Dict[str, Any],
    host_root_style: bool = False,
    role: Optional[str] = None,
    preserve_party_ids: bool = False,
    var_names: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Replace hardcoded context values with Postman macros.

    Preserves message payload as-is, only modifies context.

    When host_root_style is True, bapUri/bppUri are templated as
    "{{<bap_var>}}/bap/receiver" / "{{<bpp_var>}}/bpp/receiver" so a
    single host variable (e.g., http://beckn-router:9000 or an ngrok URL)
    drives both request targeting and callback routing.

    var_names optionally overrides the canonical variable names:
        {"bap_host_root": "buyerplatform_host_root",
         "bpp_host_root": "sellerplatform_host_root"}
    Devkits that don't declare var_names use the defaults.

    For discom-ledger roles (BUYERDISCOMLEDGER, SELLERDISCOMLEDGER), the BPP
    in the outbound on_status is the LEDGER acting as BPP-caller, so bppUri
    is templated to /bpp/caller (not /bpp/receiver).

    preserve_party_ids=True leaves context.bapId / bppId / bapUri / bppUri
    untouched. Used for seller-initiated request fixtures where the BAP and
    BPP differ from the collection's default (e.g. seller-initiated-status-
    to-seller-discom in the SELLER collection has bapId=sellerapp,
    bppId=seller-discom-ledger — both differ from the default {{bap_id}} /
    {{bpp_id}} variable values).
    """
    if not isinstance(data, dict):
        return data

    vn = var_names or {}
    bap_host_var = vn.get("bap_host_root", "bap_host_root")
    bpp_host_var = vn.get("bpp_host_root", "bpp_host_root")

    # Pick the Beckn path the BPP advertises in this collection's outbound
    # call. Default = "/bpp/receiver" (request-direction; e.g. a status
    # request arrives at the BPP's receiver). Ledger on_status collections
    # advertise /bpp/caller (callback-direction; the ledger is initiating).
    bpp_path = "/bpp/caller" if role in ("BUYERDISCOMLEDGER", "SELLERDISCOMLEDGER", "SELLERDISCOM", "BUYERDISCOM") else "/bpp/receiver"

    result = {}

    for key, value in data.items():
        if key == "context" and isinstance(value, dict):
            # Replace context fields with macros
            new_context = {}
            for ctx_key, ctx_value in value.items():
                if ctx_key == "version":
                    new_context[ctx_key] = "{{version}}"
                elif ctx_key == "domain":
                    new_context[ctx_key] = "{{domain}}"
                elif ctx_key in ("bap_id", "bapId"):
                    new_context[ctx_key] = ctx_value if preserve_party_ids else "{{bap_id}}"
                elif ctx_key in ("bap_uri", "bapUri"):
                    if preserve_party_ids:
                        new_context[ctx_key] = ctx_value
                    else:
                        new_context[ctx_key] = f"{{{{{bap_host_var}}}}}/bap/receiver" if host_root_style else "{{bap_uri}}"
                elif ctx_key in ("bpp_id", "bppId"):
                    new_context[ctx_key] = ctx_value if preserve_party_ids else "{{bpp_id}}"
                elif ctx_key in ("bpp_uri", "bppUri"):
                    if preserve_party_ids:
                        new_context[ctx_key] = ctx_value
                    else:
                        new_context[ctx_key] = f"{{{{{bpp_host_var}}}}}{bpp_path}" if host_root_style else "{{bpp_uri}}"
                elif ctx_key in ("transaction_id", "transactionId"):
                    new_context[ctx_key] = "{{transaction_id}}"
                elif ctx_key in ("message_id", "messageId"):
                    new_context[ctx_key] = "{{$guid}}"
                elif ctx_key == "timestamp":
                    new_context[ctx_key] = "{{iso_date}}"
                elif ctx_key == "ttl":
                    new_context[ctx_key] = ctx_value
                elif ctx_key in ("schema_context", "schemaContext"):
                    new_context[ctx_key] = ctx_value
                elif ctx_key == "action":
                    new_context[ctx_key] = ctx_value
                else:
                    # Preserve other context fields (e.g., location)
                    new_context[ctx_key] = replace_context_macros(ctx_value, host_root_style, role, preserve_party_ids, var_names) if isinstance(ctx_value, (dict, list)) else ctx_value

            result[key] = new_context
        elif isinstance(value, (dict, list)):
            # Recursively process nested structures in message
            result[key] = replace_context_macros(value, host_root_style, role, preserve_party_ids, var_names)
        else:
            # Preserve other fields as-is
            result[key] = value

    return result


def replace_participant_attr_macros(
    data: Any,
    attr_vars: Dict[str, Dict[str, str]],
) -> Any:
    """Replace participant attribute values with Postman variable references.

    attr_vars maps participant role → {attribute_name → postman_variable_name}.
    Only attributes present in attr_vars are replaced; all other fields are
    passed through unchanged. Example:
        {
            "buyer":        {"platformUri": "buyerplatform_host_root"},
            "seller":       {"platformUri": "sellerplatform_host_root"},
            "buyerDiscom":  {"ledgerUri":   "ledger_host_buyer"},
            "sellerDiscom": {"ledgerUri":   "ledger_host_seller"},
        }
    """
    if not attr_vars:
        return data
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == "participants" and isinstance(value, list):
                new_parts = []
                for participant in value:
                    p = dict(participant)
                    role = p.get("role", "")
                    role_attrs = attr_vars.get(role)
                    if role_attrs and isinstance(p.get("participantAttributes"), dict):
                        attrs = dict(p["participantAttributes"])
                        for attr_name, var_name in role_attrs.items():
                            if attr_name in attrs:
                                attrs[attr_name] = f"{{{{{var_name}}}}}"
                        p["participantAttributes"] = attrs
                    new_parts.append(p)
                result[key] = new_parts
            else:
                result[key] = replace_participant_attr_macros(value, attr_vars)
        return result
    elif isinstance(data, list):
        return [replace_participant_attr_macros(item, attr_vars) for item in data]
    return data


def replace_ledger_uri_macros(
    data: Any,
    buyer_var: str = "ledger_host_buyer",
    seller_var: str = "ledger_host_seller",
) -> Any:
    """Backward-compat wrapper. Prefer replace_participant_attr_macros for new devkits."""
    return replace_participant_attr_macros(data, {
        "buyerDiscom":  {"ledgerUri": buyer_var},
        "sellerDiscom": {"ledgerUri": seller_var},
    })


def create_postman_request(
    json_data: Dict[str, Any],
    action: str,
    endpoint: str,
    request_name: str,
    role: str,
    adapter_url_var: str,
    host_root_style: bool = False,
    ledger_host_buyer: Optional[str] = None,
    ledger_host_seller: Optional[str] = None,
    preserve_party_ids: bool = False,
    var_names: Optional[Dict[str, str]] = None,
    participant_attr_vars: Optional[Dict[str, Dict[str, str]]] = None,
    filename: Optional[str] = None,
    substitutions: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Create a Postman request object from JSON data.

    When `substitutions` (loaded from substitutions.yaml) and `filename` are
    both provided, all variable replacement is driven by the YAML rules and the
    legacy role-inference path is skipped entirely. For devkits without a
    substitutions.yaml the legacy path continues to work unchanged.

    Args:
        json_data: The JSON payload
        action: Action name (e.g., "discover", "on_discover")
        endpoint: API endpoint path
        request_name: Name for the request
        role: Role (BAP, BPP, UtilityBPP, ...)
        adapter_url_var: Variable name for adapter URL (e.g., "bap_caller_url")
        host_root_style: Template bapUri/bppUri as {{<bap_var>}}/bap/receiver
        ledger_host_buyer: Override for buyer ledger host (uses config default if None)
        ledger_host_seller: Override for seller ledger host (uses config default if None)
        var_names: Optional rename map for canonical variable names
        participant_attr_vars: Optional per-role attribute substitution map
        filename: Basename of the source example file (required when substitutions is set)
        substitutions: Parsed substitutions.yaml content; drives all replacements when set
    """
    if substitutions and filename:
        request_body = _apply_substitutions(json_data, filename, role, substitutions)
    else:
        # Legacy path — used for all devkits without substitutions.yaml
        request_body = replace_context_macros(json_data, host_root_style, role, preserve_party_ids, var_names)
        if participant_attr_vars:
            request_body = replace_participant_attr_macros(request_body, participant_attr_vars)
        elif ledger_host_buyer is not None or ledger_host_seller is not None:
            request_body = replace_ledger_uri_macros(request_body)

    # Format JSON, preserving the same compact-array formatting used in the
    # example payloads on disk: each item of a small repetitive array (intervals,
    # payloadDescriptors, reportDescriptors, vendorDevices, roles, participants,
    # revenueFlows) renders on a single line, plus short pure-scalar arrays
    # render inline. Larger nested structures stay expanded.
    body_raw = _format_payload(request_body)

    # BAP discover is a GET so Postman prunes the body unless explicitly disabled
    is_bap_discover = role == "BAP" and action == "discover"
    method = "GET" if is_bap_discover else "POST"

    item = {
        "name": request_name,
        "request": {
            "method": method,
            "header": [],
            "body": {
                "mode": "raw",
                "raw": body_raw,
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            },
            "url": {
                "raw": f"{{{{{adapter_url_var}}}}}/{endpoint}",
                "host": [f"{{{{{adapter_url_var}}}}}"],
                # Compound endpoints (e.g. catalog/publish) become multiple
                # path segments.
                "path": endpoint.split("/")
            },
            "description": f"{action.capitalize()} request: {request_name}"
        },
        "response": []
    }

    if is_bap_discover:
        item["protocolProfileBehavior"] = {"disableBodyPruning": True}

    return item


def scan_examples_directory(examples_dir: Path, structure: str, role: str) -> Dict[str, List[Tuple[Path, str]]]:
    """
    Scan examples directory and group JSON files by action.
    
    Args:
        examples_dir: Path to examples directory
        structure: "folders" or "flat"
        role: "BAP", "BPP", or "UtilityBPP"
    
    Returns: {action: [(filepath, request_name)]}
    """
    actions_map = {}
    
    if not examples_dir.exists():
        print(f"Error: Examples directory not found: {examples_dir}")
        return actions_map
    
    if structure == "folders":
        # Folder-based structure (ev-charging)
        for item in examples_dir.iterdir():
            if not item.is_dir():
                continue
            
            action = extract_action_from_folder(item.name, role)
            if action is None:
                continue
            
            # Find all JSON files in this folder
            json_files = list(item.glob("*.json"))
            for json_file in json_files:
                # For folder-based structure, we trust the folder name for role filtering
                # But we can still check filename as secondary filter
                request_name = get_request_name(json_file.name)
                if action not in actions_map:
                    actions_map[action] = []
                actions_map[action].append((json_file, request_name))
        
        for action, files in actions_map.items():
            print(f"Found {len(files)} example(s) for action '{action}'")
    
    else:
        # Flat structure (p2p-trading)
        json_files = list(examples_dir.glob("*.json"))
        for json_file in json_files:
            # Check if file matches role filter
            if not matches_role_filter(json_file.name, role):
                continue
            
            action = extract_action_from_filename(json_file.name, role)
            if action is None:
                continue
            
            request_name = get_request_name(json_file.name)
            if action not in actions_map:
                actions_map[action] = []
            actions_map[action].append((json_file, request_name))
        
        for action, files in actions_map.items():
            print(f"Found {len(files)} example(s) for action '{action}'")
    
    return actions_map


def get_collection_variables(devkit: str, role: str, var_names: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """Get collection variables based on devkit and role."""
    config = DEVKIT_CONFIGS[devkit]

    # For discom-ledger TSP roles, the BPP of the collection's outbound call IS
    # the ledger itself — so bpp_id / bpp_host_root variables get overridden to
    # the ledger's identity. bap_id stays pointing at the recipient platform
    # (buyerapp by default, matching the response fixtures); testers swap it
    # in postman if firing the on_status at sellerapp instead.
    bap_id_value = config["bap_id"]
    bap_host_root_value = config.get("bap_host_root")
    bpp_id_value = config["bpp_id"]
    bpp_host_root_value = config.get("bpp_host_root")
    if role == "BUYERDISCOMLEDGER":
        bpp_id_value = "buyer-discom-ledger.example.com"
        bpp_host_root_value = config.get("ledger_host_buyer", "http://buyer-discom-ledger.example.com:9000")
    elif role == "SELLERDISCOMLEDGER":
        bpp_id_value = "seller-discom-ledger.example.com"
        bpp_host_root_value = config.get("ledger_host_seller", "http://seller-discom-ledger.example.com:9000")
    elif role == "SELLERDISCOM":
        # Sellerdiscom actor pushes on_status TO the sellerdiscomledger TSP:
        # bpp = the actor, bap = the ledger.
        bpp_id_value = "sellerdiscom.example.com"
        bpp_host_root_value = config.get("sellerdiscom_host_root", "http://sellerdiscom.example.com:9000")
        bap_id_value = "seller-discom-ledger.example.com"
        bap_host_root_value = config.get("ledger_host_seller", "http://seller-discom-ledger.example.com:9000")
    elif role == "BUYERDISCOM":
        # Buyerdiscom actor pushes on_status TO the buyerdiscomledger TSP:
        # bpp = the actor, bap = the ledger.
        bpp_id_value = "buyerdiscom.example.com"
        bpp_host_root_value = config.get("buyerdiscom_host_root", "http://buyerdiscom.example.com:9000")
        bap_id_value = "buyer-discom-ledger.example.com"
        bap_host_root_value = config.get("ledger_host_buyer", "http://buyer-discom-ledger.example.com:9000")

    # var_names renames apply to BAP/BPP collections only; ledger/discom roles
    # keep generic names to avoid ambiguity (their bpp_id is the ledger, not seller).
    vn = var_names or {}
    if role in ("BAP", "BPP"):
        bap_id_key = vn.get("bap_id", "bap_id")
        bpp_id_key = vn.get("bpp_id", "bpp_id")
    else:
        bap_id_key = "bap_id"
        bpp_id_key = "bpp_id"

    variables = [
        {"key": "domain", "value": config["domain"]},
        {"key": "version", "value": "2.0.0"},
        {"key": bap_id_key, "value": bap_id_value},
        {"key": bpp_id_key, "value": bpp_id_value},
        {"key": "transaction_id", "value": config.get("transaction_id", "2b4d69aa-22e4-4c78-9f56-5a7b9e2b2002")},
        {"key": "iso_date", "value": ""}
    ]

    # Presence of bap_host_root switches templating to {{<bap_var>}}/bap/receiver.
    # For BAP/BPP roles, var_names can rename these to domain-specific names
    # (e.g. buyerplatform_host_root / sellerplatform_host_root). Ledger/discom
    # roles keep the generic names to avoid ambiguity.
    if "bap_host_root" in config:
        if role in ("BAP", "BPP"):
            bap_key = vn.get("bap_host_root", "bap_host_root")
            bpp_key = vn.get("bpp_host_root", "bpp_host_root")
        else:
            bap_key = "bap_host_root"
            bpp_key = "bpp_host_root"
        variables.append({"key": bap_key, "value": bap_host_root_value or config["bap_host_root"]})
        variables.append({"key": bpp_key, "value": bpp_host_root_value or config["bpp_host_root"]})
    else:
        variables.append({"key": "bap_uri", "value": config["bap_uri"]})
        variables.append({"key": "bpp_uri", "value": config["bpp_uri"]})
    
    # Add adapter URLs based on canonical role
    if role == "BAP":
        variables.append({"key": "bap_caller_url", "value": config["bap_caller_url"]})
    elif role == "BPP":
        variables.append({"key": "bpp_caller_url", "value": config["bpp_caller_url"]})
    elif role == "UtilityBPP":
        variables.append({"key": "bpp_caller_url", "value": config["bpp_caller_url"]})
        variables.append({"key": "bap_caller_url", "value": config["bap_caller_url"]})
    elif role == "BUYERDISCOMLEDGER":
        variables.append({"key": "buyer_ledger_bpp_caller_url", "value": config["buyer_ledger_bpp_caller_url"]})
        variables.append({"key": "buyer_ledger_bap_caller_url", "value": config["buyer_ledger_bap_caller_url"]})
        variables.append({"key": "discom_actor_id", "value": "buyerdiscom.example.com"})
        variables.append({"key": "discom_actor_host_root", "value": config.get("buyerdiscom_host_root", "http://buyerdiscom.example.com:9000")})
        variables.append({"key": "meter_request_tx_id", "value": "bdledger-status-001"})
    elif role == "SELLERDISCOMLEDGER":
        variables.append({"key": "seller_ledger_bpp_caller_url", "value": config["seller_ledger_bpp_caller_url"]})
        variables.append({"key": "seller_ledger_bap_caller_url", "value": config["seller_ledger_bap_caller_url"]})
        variables.append({"key": "discom_actor_id", "value": "sellerdiscom.example.com"})
        variables.append({"key": "discom_actor_host_root", "value": config.get("sellerdiscom_host_root", "http://sellerdiscom.example.com:9000")})
        variables.append({"key": "meter_request_tx_id", "value": "sdledger-status-001"})
    elif role == "SELLERDISCOM":
        variables.append({"key": "sellerdiscom_bpp_caller_url", "value": config["sellerdiscom_bpp_caller_url"]})
        if "ledger_host_seller" in config:
            variables.append({"key": "sellerdiscom_ledger_host_root", "value": config["ledger_host_seller"]})
    elif role == "BUYERDISCOM":
        variables.append({"key": "buyerdiscom_bpp_caller_url", "value": config["buyerdiscom_bpp_caller_url"]})
        if "ledger_host_buyer" in config:
            variables.append({"key": "buyerdiscom_ledger_host_root", "value": config["ledger_host_buyer"]})

    # Seller-initiated /bap/caller URL and discom-ledger IDs — present when the
    # SELLER (BPP-role) collection includes seller-initiated requests.
    if "seller_bap_caller_url" in config and role == "BPP":
        variables.append({"key": "seller_bap_caller_url", "value": config["seller_bap_caller_url"]})
    if "seller_discom_ledger_id" in config and role == "BPP":
        variables.append({"key": "seller_discom_ledger_id", "value": config["seller_discom_ledger_id"]})

    # Ledger host variables (wave2 and other devkits that route through a separate ledger)
    if "ledger_host_buyer" in config:
        variables.append({"key": "ledger_host_buyer", "value": config["ledger_host_buyer"]})
    if "ledger_host_seller" in config:
        variables.append({"key": "ledger_host_seller", "value": config["ledger_host_seller"]})
    # Discom platform URLs — distinct from the ledger TSP URLs; used for trade allocation.
    if "buyer_discom_host_url" in config:
        variables.append({"key": "buyer_discom_host_url", "value": config["buyer_discom_host_url"]})
    if "seller_discom_host_url" in config:
        variables.append({"key": "seller_discom_host_url", "value": config["seller_discom_host_url"]})
    if "ledger_adapter_url" in config:
        variables.append({"key": "ledger_adapter_url", "value": config["ledger_adapter_url"]})
    # Discom-ledger TSP subscriber IDs (DiscomLedgerProvider.ledgerId) —
    # emitted for all roles so contract-body fields can reference them.
    if "ledger_buyer_discom_id" in config:
        variables.append({"key": "ledger_buyer_discom_id", "value": config["ledger_buyer_discom_id"]})
    if "ledger_seller_discom_id" in config:
        variables.append({"key": "ledger_seller_discom_id", "value": config["ledger_seller_discom_id"]})
    # Discom platform discomIds (DiscomLedgerProvider.discomId).
    if "buyer_discom_subscriber_id" in config:
        variables.append({"key": "buyer_discom_subscriber_id", "value": config["buyer_discom_subscriber_id"]})
    if "seller_discom_subscriber_id" in config:
        variables.append({"key": "seller_discom_subscriber_id", "value": config["seller_discom_subscriber_id"]})

    # Trading-platform subscriber IDs / host roots — emitted for every role
    # that doesn't already define them (BUYER/SELLER get them via var_names
    # renaming), so contract-body participantId / platformUrl fields can
    # reference them in ledger/discom collections too.
    existing_keys = {v["key"] for v in variables}
    for key in ("buyerplatform_id", "sellerplatform_id",
                "buyerplatform_host_root", "sellerplatform_host_root"):
        if key in config and key not in existing_keys:
            variables.append({"key": key, "value": config[key]})

    return variables


def generate_collection(
    examples_dir: Path,
    output_path: Path,
    devkit: str,
    role: str,
    collection_name: Optional[str] = None,
    collection_description: Optional[str] = None,
    ledger_host_buyer: Optional[str] = None,
    ledger_host_seller: Optional[str] = None,
) -> None:
    """
    Generate Postman collection from examples.

    Args:
        examples_dir: Path to examples directory
        output_path: Output path for collection
        devkit: "ev-charging" or "p2p-trading"
        role: "BAP", "BPP", or "UtilityBPP"
        collection_name: Optional collection name (auto-generated if None)
        collection_description: Optional description (auto-generated if None)
        ledger_host_buyer: Override buyer discom ledger host (e.g. http://beckn-router:9000)
        ledger_host_seller: Override seller discom ledger host
    """
    config = dict(DEVKIT_CONFIGS[devkit])  # shallow copy so overrides don't mutate global
    if ledger_host_buyer is not None:
        config["ledger_host_buyer"] = ledger_host_buyer
    if ledger_host_seller is not None:
        config["ledger_host_seller"] = ledger_host_seller
    structure = config["structure"]
    host_root_style = "bap_host_root" in config
    var_names: Dict[str, str] = config.get("var_names", {})
    participant_attr_vars: Dict[str, Dict[str, str]] = config.get("participant_attr_vars", {})

    # Determine action mapping and adapter URL based on canonical role
    if role == "BAP":
        action_mapping = BAP_ACTIONS
        adapter_url_var = "bap_caller_url"
    elif role == "BPP":
        # BPP uses both callback actions and BPP-initiated actions (like publish to CDS).
        # If the devkit declares a seller_bap_caller_url, the BPP collection ALSO
        # includes BAP-side actions (status, etc.) for "seller-initiated" requests
        # where the BPP-role node plays BAP-caller in a sub-tx it originates.
        action_mapping = {**BPP_ACTIONS, **BPP_INITIATED_ACTIONS}
        if "seller_bap_caller_url" in config:
            action_mapping = {**action_mapping, **BAP_ACTIONS}
        adapter_url_var = "bpp_caller_url"
    elif role == "UtilityBPP":
        action_mapping = BAP_ACTIONS  # UtilityBPP uses BAP actions
        adapter_url_var = "bpp_caller_url"
    elif role == "BUYERDISCOMLEDGER":
        action_mapping = {"on_status": "on_status", "status": "status"}
        adapter_url_var = "buyer_ledger_bpp_caller_url"
    elif role == "SELLERDISCOMLEDGER":
        action_mapping = {"on_status": "on_status", "status": "status"}
        adapter_url_var = "seller_ledger_bpp_caller_url"
    elif role == "SELLERDISCOM":
        action_mapping = {"on_status": "on_status"}
        adapter_url_var = "sellerdiscom_bpp_caller_url"
    elif role == "BUYERDISCOM":
        # Buyer-discom actor: outbound on_status push of meter actuals from
        # the actor's /bpp/caller to the buyerdiscomledger TSP's /bap/receiver.
        action_mapping = {"on_status": "on_status"}
        adapter_url_var = "buyerdiscom_bpp_caller_url"
    else:
        raise ValueError(f"Unknown role: {role}")

    # Auto-generate collection name (uses public/alias name if caller passed
    # one; otherwise the canonical role name).
    if collection_name is None:
        collection_name = f"{devkit}.{role}-DEG"

    if collection_description is None:
        role_desc = {
            "BAP": "Buyer Application Platform",
            "BPP": "Buyer Provider Platform",
            "UtilityBPP": "Utility BPP (Transmission/Grid Provider Platform)",
            "BUYERDISCOMLEDGER": "Buyer-discom ledger TSP (emits on_status callbacks)",
            "SELLERDISCOMLEDGER": "Seller-discom ledger TSP (emits on_status callbacks)",
            "SELLERDISCOM": "Seller-discom actor (the utility itself; pushes meter actuals as on_status to the ledger TSP)",
            "BUYERDISCOM": "Buyer-discom actor (the utility itself; pushes meter actuals as on_status to the ledger TSP)",
        }
        devkit_desc = devkit
        collection_description = f"Postman collection for {role_desc[role]} implementing {devkit_desc} APIs based on Beckn Protocol v2"
    
    print(f"Scanning examples directory: {examples_dir}")
    print(f"Devkit: {devkit}, Role: {role}, Structure: {structure}")

    # Load declarative substitutions from the output directory (opt-in per collection).
    # When present, all variable replacement is driven by the YAML; legacy
    # role-inference is skipped. When absent, legacy path runs unchanged.
    substitutions = _load_substitutions(output_path.parent / "substitutions.yaml")
    if substitutions:
        print(f"  Loaded substitutions.yaml from {output_path.parent}")

    actions_map = scan_examples_directory(examples_dir, structure, role)

    if not actions_map:
        print("No valid examples found. Exiting.")
        return

    # Build collection items (folders, one per action). Per-file the URL var
    # may differ — e.g. SELLER's status has two seller-initiated requests
    # going to {{seller_bap_caller_url}}.
    collection_items = []

    # Process each action in order (include all BAP actions, even if no examples)
    all_actions = sorted(set(list(actions_map.keys()) + list(action_mapping.keys())))

    # Per-devkit endpoint overrides — e.g. Beckn v2 catalog actions are
    # compound endpoints ("publish" → "catalog/publish") on devkits whose
    # routing configs declare the compound form.
    endpoint_overrides: Dict[str, str] = config.get("endpoint_overrides", {})

    for action in all_actions:
        if action not in action_mapping:
            continue

        endpoint = endpoint_overrides.get(action, action_mapping[action])
        files_list = actions_map.get(action, [])

        action_items = []

        for json_file, request_name in sorted(files_list):
            print(f"  Processing: {json_file.name}")

            json_data = load_example_json(json_file)
            if json_data is None:
                continue

            # Seller-initiated: the BPP-role node (seller) plays BAP-caller for
            # a sub-tx it initiates (e.g. asking buyer about buyer-discom alloc,
            # or asking its own discom ledger about settlement). Routes to
            # {{seller_bap_caller_url}}; body's bap/bppId/Uri are preserved
            # literally so they don't collide with the collection's default
            # bap_id/bpp_id macro values (which point at the canonical trade
            # direction).
            is_seller_initiated = (
                role == "BPP"
                and json_file.name.startswith("seller-initiated-")
                and "seller_bap_caller_url" in config
            )
            # Ledger-initiated status requests go via /bap/caller, not /bpp/caller.
            is_ledger_status_request = (
                role in ("BUYERDISCOMLEDGER", "SELLERDISCOMLEDGER")
                and json_file.name.startswith("status-request")
            )
            _ledger_bap_url = {
                "BUYERDISCOMLEDGER": "buyer_ledger_bap_caller_url",
                "SELLERDISCOMLEDGER": "seller_ledger_bap_caller_url",
            }

            effective_caller_url_var = (
                "seller_bap_caller_url" if is_seller_initiated
                else _ledger_bap_url[role] if is_ledger_status_request
                else adapter_url_var
            )

            request = create_postman_request(
                json_data, action, endpoint, request_name, role, effective_caller_url_var, host_root_style,
                ledger_host_buyer=config.get("ledger_host_buyer"),
                ledger_host_seller=config.get("ledger_host_seller"),
                preserve_party_ids=is_seller_initiated,
                var_names=var_names or None,
                participant_attr_vars=participant_attr_vars or None,
                filename=json_file.name,
                substitutions=substitutions,
            )
            action_items.append(request)

        if action_items:
            collection_items.append({"name": action, "item": action_items})
            print(f"  Created folder '{action}' with {len(action_items)} request(s)")
    
    # Preserve the existing _postman_id so regeneration doesn't produce a spurious
    # diff. Only generate a new UUID when the output file doesn't exist yet.
    existing_id = None
    if output_path.exists():
        try:
            with output_path.open() as f:
                existing_id = json.load(f).get("info", {}).get("_postman_id")
        except Exception:
            pass
    postman_id = existing_id or str(uuid.uuid4())

    # Build collection
    collection = {
        "info": {
            "_postman_id": postman_id,
            "name": collection_name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": collection_description
        },
        "item": collection_items,
        "event": [
            {
                "listen": "prerequest",
                "script": {
                    "type": "text/javascript",
                    "exec": PRE_REQUEST_SCRIPT.split("\n")
                }
            }
        ],
        "variable": get_collection_variables(devkit, role, var_names=var_names or None)
    }
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Generated Postman collection: {output_path}")
    print(f"  Total folders: {len(collection_items)}")
    print(f"  Total requests: {sum(len(item['item']) for item in collection_items)}")
    
    return output_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Postman collection from example JSONs for a a predefined devkit and role"
    )
    parser.add_argument(
        "--devkit",
        type=str,
        choices=sorted(DEVKIT_CONFIGS.keys()),
        required=True,
        help="Devkit type"
    )
    parser.add_argument(
        "--role",
        type=str,
        choices=sorted(ROLE_ALIAS.keys()),
        required=True,
        help="Role. Legacy: 'BAP', 'BPP', 'UtilityBPP'. "
             "Business-role names (preferred for v2 LTS devkits): 'BUYER', 'SELLER'. "
             "Discom-ledger TSP collections (emits on_status callbacks): "
             "'BUYERDISCOMLEDGER', 'SELLERDISCOMLEDGER'."
    )
    parser.add_argument(
        "--examples",
        type=str,
        default=None,
        help="Path to examples directory (default: uses devkit config)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        dest="output_dir",
        help="Output directory for Postman collection (required)"
    )
    parser.add_argument(
        "--usecase",
        type=str,
        default=None,
        dest="usecase",
        help="Use-case identifier (e.g. uc1). When set, collection name becomes "
             "<devkit>-<usecase>.<role>-DEG. Overrides the devkit config default if any."
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Explicit collection name (overrides --usecase auto-generation)"
    )
    parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Collection description (default: auto-generated)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate generated collection against schema (default: True)"
    )
    parser.add_argument(
        "--no-validate",
        dest="validate",
        action="store_false",
        help="Skip schema validation"
    )
    parser.add_argument(
        "--ledger-host-buyer",
        type=str,
        default=None,
        dest="ledger_host_buyer",
        help="Buyer discom ledger host root, e.g. http://beckn-router:9000 "
             "(default: devkit config value; sets {{ledger_host_buyer}} collection variable)"
    )
    parser.add_argument(
        "--ledger-host-seller",
        type=str,
        default=None,
        dest="ledger_host_seller",
        help="Seller discom ledger host root, e.g. http://beckn-router:9000 "
             "(default: devkit config value; sets {{ledger_host_seller}} collection variable)"
    )

    args = parser.parse_args()

    # Resolve role alias: --role accepts both legacy (BAP/BPP/UtilityBPP) and
    # public business names (BUYER/SELLER/BUYERDISCOMLEDGER/SELLERDISCOMLEDGER).
    # Filters/actions key off the canonical role; the output filename and
    # collection name use the public name the user typed.
    public_role = args.role
    role = canonical_role(public_role)

    # Get devkit configuration
    config = DEVKIT_CONFIGS[args.devkit]

    # Convert to Path objects
    repo_root_dir = Path(__file__).parent.parent

    # Per-role examples path override: discom-ledger roles source from the
    # response fixtures dir (not the BAP/BPP examples dir). Devkits set
    # `<canonical_role_lower>_examples_path` to point at it.
    role_specific_path_key = f"{role.lower()}_examples_path"
    examples_path = (
        args.examples
        or config.get(role_specific_path_key)
        or config.get("examples_path")
    )
    if examples_path is None:
        raise SystemExit(
            f"No examples path configured for devkit={args.devkit}, role={role}. "
            f"Set '{role_specific_path_key}' or 'examples_path' in DEVKIT_CONFIGS, "
            f"or pass --examples."
        )
    examples_dir = repo_root_dir / examples_path

    # Generate collection name if not provided
    if args.name is not None:
        collection_name = args.name
    else:
        usecase = args.usecase or config.get("usecase")
        if usecase:
            collection_name = f"{args.devkit}-{usecase}.{public_role}-DEG"
        else:
            collection_name = f"{args.devkit}.{public_role}-DEG"

    # Construct output filename from collection name
    filename = f"{collection_name}.postman_collection.json"
    output_path = repo_root_dir / args.output_dir / filename

    print("=" * 60)
    print(f"Postman Collection Generator")
    print(f"Devkit: {args.devkit}, Role: {public_role}" + (f" (canonical: {role})" if public_role != role else ""))
    print("=" * 60)
    print()

    output_path = generate_collection(
        examples_dir=examples_dir,
        output_path=output_path,
        devkit=args.devkit,
        role=role,
        collection_name=collection_name,
        collection_description=args.description,
        ledger_host_buyer=args.ledger_host_buyer,
        ledger_host_seller=args.ledger_host_seller,
    )
    
    # Validate collection if requested
    if args.validate:
        if get_schema_store is None or process_file is None:
            print("\n⚠ Warning: Schema validation module not available, skipping validation")
        else:
            print("\n" + "=" * 60)
            print("Validating Postman collection against schema...")
            print("=" * 60)
            try:
                schema_store, attributes_schema, attribute_schemas_map = get_schema_store()
                process_file(str(output_path), schema_store, attributes_schema, attribute_schemas_map)
                print("\n✓ Schema validation completed")
            except Exception as e:
                print(f"\n⚠ Warning: Schema validation failed: {e}")
                import traceback
                traceback.print_exc()
                print("  Collection was still generated successfully")


if __name__ == "__main__":
    main()

