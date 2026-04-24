#!/usr/bin/env bash
# Run the uc1-ev-charging Arazzo workflows via Redocly Respect.
#
# Default mode (no PUBLIC_URL): payload bapUri/bppUri are rewritten to
# http://beckn-router:9000 — Caddy bridges BAP↔BPP traffic locally inside
# docker, no ngrok needed.
#
# Over-internet mode (forces public-internet traversal): set PUBLIC_URL
# to the ngrok tunnel URL fronting beckn-router:9000.
#
# Usage (from uc1-ev-charging/workflows/):
#   ./run-arazzo.sh                                                    # local-bridge mode
#   ./run-arazzo.sh -w select-through-status -v
#   PUBLIC_URL=https://your-domain.ngrok-free.dev ./run-arazzo.sh      # over-internet mode

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RUN_ARAZZO_ARGS=("$@")
# shellcheck disable=SC1091
source "$(cd "$HERE/../../.." && pwd)/scripts/run-arazzo-lib.sh"
run_arazzo "$HERE" "ev-charging" "ev-charging.arazzo.yaml"
