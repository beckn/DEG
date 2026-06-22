#!/bin/bash
# Uploads .env files to AWS Secrets Manager as flat K-V pairs.
# Run this once after terraform apply to populate secrets with real values.
#
# Usage:
#   ./seed-secrets.sh
#
# Expects these files to exist (see .env.*.example for templates):
#   scripts/.env.sandbox-bap
#   scripts/.env.sandbox-bpp
#   scripts/.env.sandbox-utilitybpp
#   scripts/.env.onix
#   scripts/.env.firebase       (plaintext JSON content of the service account file)
#   scripts/.env.ssh-key-deg    (plaintext SSH private key)
#   scripts/.env.ssh-key-sandbox (plaintext SSH private key)
#
# NOTE: PEM keys (JWT_PRIVATE_KEY, JWT_PUBLIC_KEY) must be stored as single-line
# \n-escaped strings in the .env files, e.g.:
#   JWT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIEvAIBAD...\n-----END PRIVATE KEY-----\n
set -euo pipefail

# ── Variables ─────────────────────────────────────────────────────────────────
AWS_REGION="${AWS_REGION:-ap-south-1}"
APP_ENV="${APP_ENV:-uat}"
SECRET_PREFIX="p2p-trading/${APP_ENV}"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Helpers ───────────────────────────────────────────────────────────────────

# Converts a .env file (KEY=VALUE lines) to a JSON object and upserts to Secrets Manager
upsert_kv_secret() {
  local secret_name="${SECRET_PREFIX}/$1"
  local env_file="$2"

  if [ ! -f "$env_file" ]; then
    echo "[seed] SKIP: $env_file not found — create it from the .example file"
    return
  fi

  # Build JSON object from KEY=VALUE lines (skip comments and blank lines)
  local json
  json=$(python3 - "$env_file" <<'PYEOF'
import sys, json, re
result = {}
with open(sys.argv[1]) as f:
    for line in f:
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue
        # Split only on first '='
        m = re.match(r'^([^=]+)=(.*)$', line)
        if m:
            result[m.group(1)] = m.group(2)
print(json.dumps(result))
PYEOF
)

  if aws secretsmanager describe-secret \
      --region "$AWS_REGION" \
      --secret-id "$secret_name" &>/dev/null; then
    aws secretsmanager put-secret-value \
      --region "$AWS_REGION" \
      --secret-id "$secret_name" \
      --secret-string "$json"
    echo "[seed] Updated: $secret_name"
  else
    aws secretsmanager create-secret \
      --region "$AWS_REGION" \
      --name "$secret_name" \
      --description "p2p-trading ${APP_ENV} — $1" \
      --secret-string "$json" \
      --tags "Key=Project,Value=p2p-trading" "Key=Environment,Value=${APP_ENV}" "Key=ManagedBy,Value=terraform"
    echo "[seed] Created: $secret_name"
  fi
}

# Upserts a plaintext secret (SSH key, Firebase JSON) from a file
upsert_plaintext_secret() {
  local secret_name="${SECRET_PREFIX}/$1"
  local file="$2"

  if [ ! -f "$file" ]; then
    echo "[seed] SKIP: $file not found"
    return
  fi

  local content
  content=$(cat "$file")

  if aws secretsmanager describe-secret \
      --region "$AWS_REGION" \
      --secret-id "$secret_name" &>/dev/null; then
    aws secretsmanager put-secret-value \
      --region "$AWS_REGION" \
      --secret-id "$secret_name" \
      --secret-string "$content"
    echo "[seed] Updated: $secret_name"
  else
    aws secretsmanager create-secret \
      --region "$AWS_REGION" \
      --name "$secret_name" \
      --description "p2p-trading ${APP_ENV} — $1" \
      --secret-string "$content" \
      --tags "Key=Project,Value=p2p-trading" "Key=Environment,Value=${APP_ENV}" "Key=ManagedBy,Value=terraform"
    echo "[seed] Created: $secret_name"
  fi
}

# ── Seed All Secrets ──────────────────────────────────────────────────────────
echo "[seed] Seeding secrets to ${SECRET_PREFIX}/* in ${AWS_REGION}..."

upsert_kv_secret "sandbox-bap"        "${SCRIPTS_DIR}/.env.sandbox-bap"
upsert_kv_secret "sandbox-bpp"        "${SCRIPTS_DIR}/.env.sandbox-bpp"
upsert_kv_secret "sandbox-utilitybpp" "${SCRIPTS_DIR}/.env.sandbox-utilitybpp"
upsert_kv_secret "onix"               "${SCRIPTS_DIR}/.env.onix"
upsert_plaintext_secret "firebase"         "${SCRIPTS_DIR}/.env.firebase"
upsert_plaintext_secret "ssh-key-deg"      "${SCRIPTS_DIR}/.env.ssh-key-deg"
upsert_plaintext_secret "ssh-key-sandbox"  "${SCRIPTS_DIR}/.env.ssh-key-sandbox"

echo "[seed] Done."
