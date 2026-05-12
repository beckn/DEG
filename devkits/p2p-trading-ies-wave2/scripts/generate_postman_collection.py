#!/usr/bin/env python3
"""
Thin wrapper around DEG/scripts/generate_postman_collection.py.

Usage:
  python3 scripts/generate_postman_collection.py --role BAP
  python3 scripts/generate_postman_collection.py --role BPP

  # Override ledger host roots (default: http://beckn-router:9000 for both)
  python3 scripts/generate_postman_collection.py --role BAP \\
    --ledger-host-buyer http://my-buyer-ledger:9000 \\
    --ledger-host-seller http://my-seller-ledger:9000
"""

import subprocess
import sys
from pathlib import Path

DEVKIT_ROOT = Path(__file__).parent.parent
REPO_ROOT = DEVKIT_ROOT.parent.parent
TOP_LEVEL_SCRIPT = REPO_ROOT / "scripts" / "generate_postman_collection.py"

ROLE = None
LEDGER_HOST_BUYER = None
LEDGER_HOST_SELLER = None

i = 1
while i < len(sys.argv):
    if sys.argv[i] == "--role" and i + 1 < len(sys.argv):
        ROLE = sys.argv[i + 1]
        i += 2
    elif sys.argv[i] == "--ledger-host-buyer" and i + 1 < len(sys.argv):
        LEDGER_HOST_BUYER = sys.argv[i + 1]
        i += 2
    elif sys.argv[i] == "--ledger-host-seller" and i + 1 < len(sys.argv):
        LEDGER_HOST_SELLER = sys.argv[i + 1]
        i += 2
    else:
        i += 1

if ROLE is None:
    print("Usage: python3 scripts/generate_postman_collection.py --role BAP|BPP")
    print("       [--ledger-host-buyer <url>] [--ledger-host-seller <url>]")
    sys.exit(1)

usecase = "uc1"
output_dir = str(DEVKIT_ROOT / usecase / "postman")
cmd = [
    sys.executable, str(TOP_LEVEL_SCRIPT),
    "--devkit", "p2p-trading-ies-wave2",
    "--role", ROLE,
    "--usecase", usecase,
    "--output-dir", output_dir,
    "--no-validate",
]
if LEDGER_HOST_BUYER:
    cmd += ["--ledger-host-buyer", LEDGER_HOST_BUYER]
if LEDGER_HOST_SELLER:
    cmd += ["--ledger-host-seller", LEDGER_HOST_SELLER]

ret = subprocess.call(cmd)
sys.exit(ret)
