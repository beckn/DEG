#!/usr/bin/env bash
# Run the uc3-streaming Arazzo workflows via Redocly Respect.
#
# Usage (from uc3-streaming/workflows/):
#   ./run-arazzo.sh                        # all workflows, local-bridge mode
#   ./run-arazzo.sh -w publish-catalog -v
#   ./run-arazzo.sh -w confirm-mqtt -v
#   ./run-arazzo.sh -w confirm-kafka -v
#   ./run-arazzo.sh -w confirm-api -v
#   ./run-arazzo.sh -w confirm-datalake -v
#   ./run-arazzo.sh -w credential-rotation -v

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RUN_ARAZZO_ARGS=("$@")
# shellcheck disable=SC1091
source "$(cd "$HERE/../../.." && pwd)/scripts/run-arazzo-lib.sh"
run_arazzo "$HERE" "data-exchange-streaming" "data-exchange-streaming.arazzo.yaml"
