#!/usr/bin/env bash
# Shared Arazzo runner for DEG devkits.
#
# Sourced by per-usecase run-arazzo.sh wrappers; drives Redocly Respect,
# rewrites payload BAP/BPP URIs so BAP↔BPP traffic flows through the local
# beckn-router (or an ngrok tunnel), and post-processes respect's JSON log
# to fail the run on any NACK. Redocly Respect crashes with "Maximum call
# stack size exceeded" in 2.14+ (successCriteria evaluator bug) and requires
# --stack-size=65536 for its spec dereferencer on the beckn OpenAPI spec.
# Pinned to 2.38.0 via a cached npm install; NACK and sandbox-callback
# checks are done out-of-band below.
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
  local usecase_root devkit_root uc_name
  usecase_root="$(cd "$here/.." && pwd)"
  devkit_root="$(cd "$usecase_root/.." && pwd)"
  uc_name="$(basename "$usecase_root")"  # e.g. "uc1", "uc1-meter-data"

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

  # Preserve the usecase directory level so $ref relative paths in the arazzo
  # resolve identically in the tmpdir and the real repo.
  # e.g. arazzo at $work/uc1/workflows/ means:
  #   ../examples/      → $work/uc1/examples/
  #   ../../responses/  → $work/responses/
  mkdir -p "$work/$uc_name/workflows" "$work/$uc_name/examples"

  # Copy the Arazzo file and all sibling YAML/JSON files (local OpenAPI stubs,
  # substitution files, etc.) so relative $ref paths resolve in the tmpdir.
  find "$usecase_root/workflows" -maxdepth 1 \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
    -exec cp {} "$work/$uc_name/workflows/" \;

  # Shared cache directory for both the pinned Redocly install and the
  # processed beckn.yaml (both persist across runs in /tmp).
  local redocly_cache="/tmp/redocly-cli-2.38.0"
  local redocly_bin="$redocly_cache/node_modules/.bin/redocly"

  # Prepare a circular-ref-free copy of beckn.yaml for Redocly's dereferencer.
  # The upstream spec has intentional circular $ref chains (Offer→AddOn→Offer,
  # GeoJSONGeometry self-ref, Error.cause→Error) that cause infinite recursion
  # and OOM in Redocly's spec dereferencer. We download the spec once, run a
  # DFS back-edge detector that replaces only the cycling $ref entries with {},
  # and cache the result at $redocly_cache/beckn-processed.yaml. All non-circular
  # $ref entries are left intact so Redocly can still validate real schemas.
  # The original Arazzo file keeps the authoritative URL; only the tmpdir copy
  # is patched to point at the processed local file.
  local beckn_processed="$redocly_cache/beckn-processed.yaml"
  if [ ! -f "$beckn_processed" ]; then
    echo "Downloading beckn.yaml and breaking circular \$refs (first run only) ..."
    python3 - "$beckn_processed" <<'BREAK_CYCLES_PY'
import sys, yaml
from urllib.request import urlopen
sys.setrecursionlimit(5000)

BECKN_URL = (
    "https://raw.githubusercontent.com/beckn/protocol-specifications-v2"
    "/refs/heads/main/api/v2.0.0/beckn.yaml"
)
print(f"  Fetching {BECKN_URL} ...", flush=True)
doc = yaml.safe_load(urlopen(BECKN_URL, timeout=30).read().decode())
schemas = (doc.get("components") or {}).get("schemas") or {}

def collect_refs(obj, out=None):
    """Return list of (dict_obj, target_schema_name) for every local $ref."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        ref = obj.get("$ref", "")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            out.append((obj, ref[len("#/components/schemas/"):]))
        else:
            for v in obj.values():
                collect_refs(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_refs(v, out)
    return out

# Build per-schema adjacency once (list of (ref_dict, target_name) tuples).
adj = {name: collect_refs(schema) for name, schema in schemas.items()}

# DFS with 3-colour marking; back edges (GRAY→GRAY) are the cycle closures.
WHITE, GRAY, BLACK = 0, 1, 2
colour = {n: WHITE for n in schemas}
broken = 0

def dfs(name):
    global broken
    if colour.get(name) != WHITE:
        return
    colour[name] = GRAY
    for ref_dict, target in adj.get(name, []):
        if colour.get(target) == GRAY:
            ref_dict.clear()   # replace {$ref: ...} with {} in-place
            broken += 1
        else:
            dfs(target)
    colour[name] = BLACK

for name in list(schemas):
    dfs(name)

print(f"  Broke {broken} circular $ref(s).", flush=True)
out_path = sys.argv[1]
with open(out_path, "w", encoding="utf-8") as fh:
    yaml.dump(doc, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)
print(f"  Cached → {out_path}", flush=True)
BREAK_CYCLES_PY
  fi

  # Copy the processed spec into the tmpdir so the patched Arazzo can $ref it.
  cp "$beckn_processed" "$work/$uc_name/workflows/beckn-processed.yaml"

  # Patch the tmpdir Arazzo copy to use the local processed spec.
  python3 -c "
import re, pathlib, sys
f = pathlib.Path(sys.argv[1])
txt = f.read_text()
patched = re.sub(
    r'url: https://raw\.githubusercontent\.com/beckn/[^\n]*/beckn\.yaml',
    'url: ./beckn-processed.yaml',
    txt,
)
f.write_text(patched)
n = txt.count('beckn.yaml')
print(f'Patched {n} sourceDescription URL(s) → beckn-processed.yaml (schema validation enabled)')
" "$work/$uc_name/workflows/$arazzo"

  # Shared URI-patching helper — rewrites context.bapUri/bppUri and
  # participant ledgerUris so each participant lives on its own hostname
  # (matching its Beckn subscriberId). Each payload's own context.bapId /
  # bppId is used as the hostname, so the BAP/BPP URLs line up with the
  # dedi registry entries (which key off subscriberId). beckn-router must
  # advertise these subscriberId hostnames as network aliases on both
  # docker networks — see install/docker-compose.yml.
  local patch_py='
import json, os, sys, pathlib
from urllib.parse import urlparse, urlunparse
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
pub = os.environ["PUBLIC_URL"]
u = urlparse(pub)

def base_for(host):
    netloc = f"{host}:{u.port}" if u.port else host
    return urlunparse((u.scheme, netloc, "", "", "", ""))

# Wave2 split-discom: the ledgerUri for a discom-role participant is the
# host base of the discom node (scheme + host[:port], no path). The recorder
# appends /bap/receiver or /bpp/caller per direction. These hostnames are
# stable across wave2 use cases; demand-flex has no participants with these
# roles so the lookup is a no-op there.
discom_ledger_uri = {
    "sellerDiscom": base_for("seller-discom-ledger.example.com"),
    "buyerDiscom":  base_for("buyer-discom-ledger.example.com"),
}

def pick(ctx, *keys):
    for k in keys:
        if k in ctx and ctx[k]:
            return ctx[k]
    return None

for f in sorted(src.rglob("*.json")):
    rel = f.relative_to(src)
    out = dst / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    d = json.load(open(f))
    if not isinstance(d, dict):
        json.dump(d, open(out, "w"), indent=2)
        continue
    ctx = d.get("context")
    if isinstance(ctx, dict):
        bap_id = pick(ctx, "bapId", "bap_id")
        bpp_id = pick(ctx, "bppId", "bpp_id")
        if bap_id:
            bap_base = base_for(bap_id) + "/bap/receiver"
            if "bapUri"  in ctx: ctx["bapUri"]  = bap_base
            if "bap_uri" in ctx: ctx["bap_uri"] = bap_base
        if bpp_id:
            bpp_base = base_for(bpp_id) + "/bpp/receiver"
            if "bppUri"  in ctx: ctx["bppUri"]  = bpp_base
            if "bpp_uri" in ctx: ctx["bpp_uri"] = bpp_base
    participants = (d.get("message", {}) or {}).get("contract", {}).get("participants") or []
    for p in participants:
        attrs = p.get("participantAttributes")
        if isinstance(attrs, dict) and "ledgerUri" in attrs and p.get("role") in discom_ledger_uri:
            attrs["ledgerUri"] = discom_ledger_uri[p["role"]]
    json.dump(d, open(out, "w"), indent=2)
'

  PUBLIC_URL="$public_url" python3 -c "$patch_py" "$usecase_root/examples" "$work/$uc_name/examples"

  # Copy devkit-level responses/ when present (wave2 split-discom layout puts
  # discom on_* fixtures here; demand-flex uses per-uc responses mounted
  # directly into sandbox-bpp and does NOT need this copy).
  # Placed at $work/responses/ so ../../responses/ from $work/<uc>/workflows/
  # resolves correctly.
  # NOTE: copy verbatim — the fixtures encode discom self-identifying contexts
  # (e.g. context.bppId = seller-discom-ledger) that the generic URI rewriter
  # would clobber by assuming bppId always means the original BPP.
  if [ -d "$devkit_root/responses" ]; then
    cp -R "$devkit_root/responses" "$work/responses"
  fi

  local respect_args=()
  if [ "${#RUN_ARAZZO_ARGS[@]}" -gt 0 ]; then
    respect_args+=("${RUN_ARAZZO_ARGS[@]}")
  fi

  # Install a pinned Redocly into the shared cache (also used for beckn-processed.yaml).
  # Redocly 2.14+ has a successCriteria evaluator bug ("Maximum call stack size exceeded").
  if [ ! -x "$redocly_bin" ]; then
    echo "Installing @redocly/cli@2.38.0 into $redocly_cache ..."
    mkdir -p "$redocly_cache"
    npm install --prefix "$redocly_cache" "@redocly/cli@2.38.0" \
      --no-save --no-audit --no-fund --silent
  fi

  local json_out="$work/respect-output.json"
  local respect_exit
  # Capture an RFC3339 timestamp BEFORE the run so the sandbox-callback log
  # scan below filters out any noise from earlier runs.
  local respect_started_at
  respect_started_at="$(date -u +%Y-%m-%dT%H:%M:%S.%NZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)"
  set +e
  if [ "$public_url" = "http://beckn-router:9000" ]; then
    node --stack-size=65536 --max-old-space-size=8192 "$redocly_bin" respect \
      "$work/$uc_name/workflows/$arazzo" \
      -J "$json_out" \
      ${respect_args[@]+"${respect_args[@]}"}
  else
    node --stack-size=65536 --max-old-space-size=8192 "$redocly_bin" respect \
      "$work/$uc_name/workflows/$arazzo" \
      -J "$json_out" \
      -S "beckn-bap-caller=$public_url/bap/caller" \
      -S "beckn-bpp-caller=$public_url/bpp/caller" \
      ${respect_args[@]+"${respect_args[@]}"}
  fi
  respect_exit=$?
  set -e

  local nack_status=0
  set +e
  python3 - "$json_out" <<'PY'
import json, sys
log_path = sys.argv[1]
try:
    data = json.load(open(log_path))
except Exception as e:
    print(f"NACK check: unable to read respect JSON log ({e})")
    sys.exit(0)
import re
nacks = []
expected = []
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
            # Negative-path steps declare the NACK they expect
            # (successCriteria: $statusCode == 4xx); a passing check makes
            # the NACK the intended outcome rather than a failure.
            expects_nack = any(
                c.get('passed') and re.search(r'\$statusCode\s*==\s*4\d\d', json.dumps(c))
                for c in step.get('checks') or []
            )
            if is_nack and expects_nack:
                expected.append((wf.get('workflowId'), step.get('stepId'), status))
            elif is_nack:
                nacks.append((wf.get('workflowId'), step.get('stepId'), status))
for wf_id, step_id, status in expected:
    print(f"NACK check: expected NACK — {wf_id} / {step_id}  (HTTP {status})")
if nacks:
    print("\nNACK check: FAILED — the following steps returned a NACK/error response:")
    for wf_id, step_id, status in nacks:
        print(f"  - {wf_id} / {step_id}  (HTTP {status})")
    sys.exit(1)
print("\nNACK check: PASSED — all steps returned ACK.")
PY
  nack_status=$?
  set -e

  # Sandbox-callback check: the sandbox (bpp or ledger) emits on_* callbacks
  # asynchronously after each request. If the BPP caller or the BAP receiver
  # rejects the on_* payload (schema validation, signing, policy, etc.), the
  # sandbox's axios.post catches the error and logs it as
  # "Request failed with status code <4xx/5xx>" or "AxiosError".
  # Give async callbacks ~3s to flush, then scan sandbox-bpp container logs
  # since respect_started_at for those error markers.
  local sandbox_status=0
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx sandbox-bpp; then
    sleep 3
    local sandbox_logs
    sandbox_logs="$(docker logs --since "$respect_started_at" sandbox-bpp 2>&1 || true)"
    if echo "$sandbox_logs" | grep -Eq 'Request failed with status code|AxiosError'; then
      echo
      echo "Sandbox-callback check: FAILED — sandbox-bpp got a non-2xx when posting an on_* payload."
      echo "  This means a fixture under devkits/<devkit>/.../responses/bpp/ failed validation at"
      echo "  the BPP caller (or the BAP receiver). Offending log lines:"
      echo "$sandbox_logs" | grep -E 'Request failed with status code|AxiosError|on_' | head -40 | sed 's/^/    /'
      sandbox_status=1
    else
      echo "Sandbox-callback check: PASSED — sandbox-bpp on_* callbacks accepted by BPP caller and BAP receiver."
    fi
  fi

  if [ "$nack_status" -ne 0 ] || [ "$sandbox_status" -ne 0 ]; then
    return 1
  fi
  return "$respect_exit"
}
