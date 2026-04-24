#!/usr/bin/env python3
"""
Thin wrapper around DEG/scripts/generate_postman_collection.py.

Usage:
  python3 scripts/generate_postman_collection.py --role BAP
  python3 scripts/generate_postman_collection.py --role BPP
"""

import subprocess
import sys
from pathlib import Path

DEVKIT_ROOT = Path(__file__).parent.parent
REPO_ROOT = DEVKIT_ROOT.parent.parent
TOP_LEVEL_SCRIPT = REPO_ROOT / "scripts" / "generate_postman_collection.py"

ROLE = None
for i, arg in enumerate(sys.argv):
    if arg == "--role" and i + 1 < len(sys.argv):
        ROLE = sys.argv[i + 1]

if ROLE is None:
    print("Usage: python3 scripts/generate_postman_collection.py --role BAP|BPP")
    sys.exit(1)

usecase = "uc1-p2p-enrollment"
output_dir = str(DEVKIT_ROOT / usecase / "postman")
cmd = [
    sys.executable, str(TOP_LEVEL_SCRIPT),
    "--devkit", "p2p-enrollment",
    "--role", ROLE,
    "--output-dir", output_dir,
    "--name", f"p2p-enrollment-{usecase}.{ROLE}-DEG",
    "--no-validate",
]
ret = subprocess.call(cmd)
sys.exit(ret)
