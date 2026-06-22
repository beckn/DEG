#!/bin/bash
# Fetches secrets from AWS Secrets Manager and writes .secrets/*.env files.
# Called by bootstrap.sh and after_install.sh. Idempotent.
set -euo pipefail

# ── Variables ─────────────────────────────────────────────────────────────────
AWS_REGION="${AWS_REGION:-ap-south-1}"
APP_ENV="${APP_ENV:-uat}"
SECRET_PREFIX="p2p-trading/${APP_ENV}"
INSTALL_PATH="${INSTALL_PATH:-/opt/app/deg/testnet/p2p-trading-interdiscom-devkit/install}"
FIREBASE_HOST_PATH="${FIREBASE_HOST_PATH:-/opt/app/firebase}"
SECRETS_DIR="${INSTALL_PATH}/.secrets"

# ── Setup ─────────────────────────────────────────────────────────────────────
mkdir -p "$SECRETS_DIR" "$FIREBASE_HOST_PATH"
chmod 700 "$SECRETS_DIR"

# ── Helpers ───────────────────────────────────────────────────────────────────

# Fetches a K-V secret and writes a .env file.
# PEM keys must be stored in Secrets Manager with \n-escaped newlines (single-line strings).
fetch_kv_secret() {
  local secret_name="$1"
  local output_file="$2"

  # Tolerate absent secrets (e.g. sandbox-utilitybpp is not deployed): write an
  # empty env file so `env_file:` still resolves, and skip rather than abort.
  if ! aws secretsmanager describe-secret --region "$AWS_REGION" \
        --secret-id "${SECRET_PREFIX}/${secret_name}" >/dev/null 2>&1; then
    : > "$output_file"; chmod 600 "$output_file"
    echo "[fetch-secrets] SKIP (no secret): ${SECRET_PREFIX}/${secret_name} — wrote empty $output_file"
    return 0
  fi

  local tmp_json
  tmp_json="$(mktemp)"
  aws secretsmanager get-secret-value \
    --region "$AWS_REGION" \
    --secret-id "${SECRET_PREFIX}/${secret_name}" \
    --query SecretString \
    --output text > "$tmp_json"

  # Quoted heredoc — the script is passed to python verbatim (no shell escaping).
  python3 - "$tmp_json" <<'PYEOF' > "$output_file"
import sys, json
data = json.load(open(sys.argv[1]))
for k, v in data.items():
    v = str(v)
    # Normalize \n-escaped strings into real newlines so output is uniform
    # regardless of how the secret was stored in Secrets Manager.
    if '\\n' in v and '\n' not in v:
        v = v.replace('\\n', '\n')
    if '\n' in v:
        # Multi-line value (e.g. PEM JWT keys): wrap in double quotes so dotenv
        # preserves the newlines. NOTE: the resulting file is NOT parseable by
        # Compose 'env_file:' — the app loads it via dotenv (mounted as /app/.env).
        esc = v.replace('\\', '\\\\').replace('"', '\\"')
        print(f'{k}="{esc}"')
    else:
        print(f'{k}={v}')
PYEOF

  rm -f "$tmp_json"
  chmod 600 "$output_file"
  echo "[fetch-secrets] Written: $output_file"
}

# ── Fetch Service Secrets ─────────────────────────────────────────────────────
fetch_kv_secret "sandbox-bap"        "${SECRETS_DIR}/sandbox-bap.env"
fetch_kv_secret "sandbox-bpp"        "${SECRETS_DIR}/sandbox-bpp.env"
fetch_kv_secret "sandbox-utilitybpp" "${SECRETS_DIR}/sandbox-utilitybpp.env"
fetch_kv_secret "onix"               "${SECRETS_DIR}/onix.env"

# ── Compose-Level .env ────────────────────────────────────────────────────────
# docker compose auto-loads install/.env for variable substitution (e.g. ${AWS_REGION})
cat > "${INSTALL_PATH}/.env" <<EOF
AWS_REGION=${AWS_REGION}
EOF
chmod 600 "${INSTALL_PATH}/.env"
echo "[fetch-secrets] Written: ${INSTALL_PATH}/.env"

# ── Firebase Service Account ──────────────────────────────────────────────────
FIREBASE_FILE="${FIREBASE_HOST_PATH}/terra-rex-82a58-firebase-adminsdk-fbsvc-3aa42b9281.json"
aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "${SECRET_PREFIX}/firebase" \
  --query SecretString \
  --output text > "$FIREBASE_FILE"
chmod 600 "$FIREBASE_FILE"
echo "[fetch-secrets] Written: $FIREBASE_FILE"

echo "[fetch-secrets] Done."
