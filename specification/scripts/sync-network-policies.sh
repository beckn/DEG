#!/usr/bin/env bash
# Sync devkit-bundled network policies from their canonical source.
#
# The demand-flex devkit runs `opapolicychecker` against a LOCAL file mounted
# into the onix container (devkits/demand-flex/policies/), NOT the canonical
# rego under specification/policies/. That bundled copy must track the
# canonical or the devkit silently enforces a stale rule set. This script
# regenerates every bundled copy from its canonical source with a banner.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# canonical  ->  devkit bundled copy
sync_one() {
  local src="$1" dst="$2"
  {
    echo "# ⚠️  AUTO-SYNCED COPY — DO NOT EDIT."
    echo "# Generated from ${src#"$ROOT/"}"
    echo "# Regenerate: specification/scripts/sync-network-policies.sh"
    echo "#"
    cat "$ROOT/$src"
  } > "$ROOT/$dst"
  echo "synced  $dst"
}

sync_one specification/policies/demand-flex-networkpolicy.rego \
         devkits/demand-flex/policies/demand_flex_networkpolicy.rego
