#!/usr/bin/env bash
# Run the usecase2 Arazzo workflows via Redocly Respect, either against the
# local docker stack (default) or against the public URL exposed by the
# over-internet docker compose + ngrok tunnel.
#
# Usage (from usecase2/workflows/):
#   ./run-arazzo.sh                                    # run all workflows
#   ./run-arazzo.sh -w select-through-confirm -v       # single workflow, verbose
#
# Over-the-internet mode:
#   PUBLIC_URL=https://your-domain.ngrok-free.dev ./run-arazzo.sh
#
# When PUBLIC_URL is set, the wrapper materialises a tmpdir with a copy of the
# arazzo file and patched example payloads (docker-DNS bapUri/bppUri rewritten
# to the public URL) and runs respect against that, so the source examples on
# disk stay untouched. Server URLs (-S) are also flipped to the public URL.

set -euo pipefail

USECASE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESPECT_ARGS=(--severity 'SCHEMA_CHECK=off' "$@")

if [ -z "${PUBLIC_URL:-}" ]; then
  echo "Mode: local docker (default x-serverUrl)"
  exec npx --yes @redocly/cli respect \
    "$USECASE_ROOT/workflows/data-exchange.arazzo.yaml" \
    "${RESPECT_ARGS[@]}"
fi

PUBLIC_URL="${PUBLIC_URL%/}"
echo "Mode: over-internet via $PUBLIC_URL (payloads patched in tmpdir)"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/data-exchange-arazzo-XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/workflows" "$WORK/examples"

cp "$USECASE_ROOT/workflows/data-exchange.arazzo.yaml" "$WORK/workflows/"

PUBLIC_URL="$PUBLIC_URL" python3 - "$USECASE_ROOT/examples" "$WORK/examples" <<'PY'
import json, os, sys, pathlib
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pub = os.environ['PUBLIC_URL']
for f in sorted(src.glob('*.json')):
    d = json.load(open(f))
    ctx = d.get('context', {})
    if ctx.get('bapUri') == 'http://onix-bap:8081/bap/receiver':
        ctx['bapUri'] = pub + '/bap/receiver'
    if ctx.get('bppUri') == 'http://onix-bpp:8082/bpp/receiver':
        ctx['bppUri'] = pub + '/bpp/receiver'
    json.dump(d, open(dst / f.name, 'w'), indent=2)
PY

exec npx --yes @redocly/cli respect \
  "$WORK/workflows/data-exchange.arazzo.yaml" \
  -S "beckn-bap-caller=$PUBLIC_URL/bap/caller" \
  -S "beckn-bpp-caller=$PUBLIC_URL/bpp/caller" \
  "${RESPECT_ARGS[@]}"
