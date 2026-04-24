#!/usr/bin/env bash
# Shared Arazzo runner for DEG devkits.
#
# Sourced by per-usecase run-arazzo.sh wrappers; drives Redocly Respect,
# rewrites payload BAP/BPP URIs so BAP↔BPP traffic flows through the local
# beckn-router (or an ngrok tunnel), and post-processes respect's JSON log
# to fail the run on any NACK. Native successCriteria crashed respect with
# "Maximum call stack size exceeded" in both 2.14 and 2.29, so the NACK
# check is done out-of-band here.
#
# Usage from a wrapper:
#   set -euo pipefail
#   HERE="$(cd "$(dirname "$0")" && pwd)"
#   RUN_ARAZZO_ARGS=("$@")
#   source "$(cd "$HERE/../../.." && pwd)/scripts/run-arazzo-lib.sh"
#   run_arazzo "$HERE" "<devkit-slug>" "<arazzo-filename>"
#
# Environment:
#   PUBLIC_URL — optional ngrok tunnel URL fronting beckn-router:9000.
#                Defaults to http://beckn-router:9000 (local-bridge mode).
#   RUN_ARAZZO_ARGS — extra args forwarded to respect (e.g. -w, -v).

run_arazzo() {
  local here="$1"
  local devkit="$2"
  local arazzo="$3"
  local usecase_root
  usecase_root="$(cd "$here/.." && pwd)"

  local public_url="${PUBLIC_URL:-http://beckn-router:9000}"
  public_url="${public_url%/}"

  if [ "$public_url" = "http://beckn-router:9000" ]; then
    echo "Mode: local-bridge via beckn-router (payloads patched in tmpdir)"
  else
    echo "Mode: over-internet via $public_url (payloads patched in tmpdir)"
  fi

  local work
  work="$(mktemp -d "${TMPDIR:-/tmp}/${devkit}-arazzo-XXXXXX")"
  trap "rm -rf \"$work\"" EXIT
  mkdir -p "$work/workflows" "$work/examples"

  cp "$usecase_root/workflows/$arazzo" "$work/workflows/"

  PUBLIC_URL="$public_url" python3 - "$usecase_root/examples" "$work/examples" <<'PY'
import json, os, sys, pathlib
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pub = os.environ['PUBLIC_URL']
# rglob to support both flat (data-exchange) and nested (ev-charging) layouts.
# Both snake_case (p2p-trading-ies-wave1) and camelCase URI keys are handled.
for f in sorted(src.rglob('*.json')):
    rel = f.relative_to(src)
    out = dst / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    d = json.load(open(f))
    ctx = d.get('context') if isinstance(d, dict) else None
    if isinstance(ctx, dict):
        if 'bapUri' in ctx:
            ctx['bapUri'] = pub + '/bap/receiver'
        if 'bppUri' in ctx:
            ctx['bppUri'] = pub + '/bpp/receiver'
        if 'bap_uri' in ctx:
            ctx['bap_uri'] = pub + '/bap/receiver'
        if 'bpp_uri' in ctx:
            ctx['bpp_uri'] = pub + '/bpp/receiver'
    json.dump(d, open(out, 'w'), indent=2)
PY

  local respect_args=(--severity 'SCHEMA_CHECK=off')
  if [ "${#RUN_ARAZZO_ARGS[@]}" -gt 0 ]; then
    respect_args+=("${RUN_ARAZZO_ARGS[@]}")
  fi

  local json_out="$work/respect-output.json"
  local respect_exit
  set +e
  if [ "$public_url" = "http://beckn-router:9000" ]; then
    npx --yes @redocly/cli respect \
      "$work/workflows/$arazzo" \
      -J "$json_out" \
      "${respect_args[@]}"
  else
    npx --yes @redocly/cli respect \
      "$work/workflows/$arazzo" \
      -J "$json_out" \
      -S "beckn-bap-caller=$public_url/bap/caller" \
      -S "beckn-bpp-caller=$public_url/bpp/caller" \
      "${respect_args[@]}"
  fi
  respect_exit=$?
  set -e

  python3 - "$json_out" "$respect_exit" <<'PY'
import json, sys
log_path, respect_exit = sys.argv[1], int(sys.argv[2])
try:
    data = json.load(open(log_path))
except Exception as e:
    print(f"NACK check: unable to read respect JSON log ({e})")
    sys.exit(respect_exit)
nacks = []
for _, file_data in data.get('files', {}).items():
    for wf in file_data.get('executedWorkflows', []):
        for step in wf.get('executedSteps', []):
            resp = step.get('response') or {}
            body = resp.get('body')
            status = resp.get('statusCode')
            body_str = json.dumps(body) if not isinstance(body, str) else body
            is_nack = (
                isinstance(status, int) and status >= 400
            ) or (body_str and '"NACK"' in body_str)
            if is_nack:
                nacks.append((wf.get('workflowId'), step.get('stepId'), status))
if nacks:
    print("\nNACK check: FAILED — the following steps returned a NACK/error response:")
    for wf_id, step_id, status in nacks:
        print(f"  - {wf_id} / {step_id}  (HTTP {status})")
    sys.exit(1)
print("\nNACK check: PASSED — all steps returned ACK.")
sys.exit(respect_exit)
PY
}
