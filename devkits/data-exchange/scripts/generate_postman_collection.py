#!/usr/bin/env python3
"""
Thin wrapper around DEG/scripts/generate_postman_collection.py.

Usage:
  python3 scripts/generate_postman_collection.py --role BAP
  python3 scripts/generate_postman_collection.py --role BPP
  python3 scripts/generate_postman_collection.py --role BAP --usecase uc2-regulatory-data
"""

import subprocess
import sys
from pathlib import Path

DEVKIT_ROOT = Path(__file__).parent.parent
REPO_ROOT = DEVKIT_ROOT.parent.parent
TOP_LEVEL_SCRIPT = REPO_ROOT / "scripts" / "generate_postman_collection.py"

ROLE = None
USECASE = None
for i, arg in enumerate(sys.argv):
    if arg == "--role" and i + 1 < len(sys.argv):
        ROLE = sys.argv[i + 1]
    if arg == "--usecase" and i + 1 < len(sys.argv):
        USECASE = sys.argv[i + 1]

if ROLE is None:
    print("Usage: python3 scripts/generate_postman_collection.py --role BAP|BPP [--usecase uc1-meter-data|uc2-regulatory-data]")
    sys.exit(1)

usecases = [USECASE] if USECASE else ["uc1-meter-data", "uc2-regulatory-data"]

for uc in usecases:
    devkit = f"data-exchange-{uc}"
    output_dir = str(DEVKIT_ROOT / uc / "postman")
    cmd = [
        sys.executable, str(TOP_LEVEL_SCRIPT),
        "--devkit", devkit,
        "--role", ROLE,
        "--output-dir", output_dir,
        "--name", f"data-exchange-{uc}.{ROLE}-DEG",
        "--no-validate",
    ]
    ret = subprocess.call(cmd)
    if ret != 0:
        sys.exit(ret)
