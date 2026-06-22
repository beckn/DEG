#!/bin/bash
# Checks Docker health status for all p2p-trading containers and publishes
# custom CloudWatch metrics. Run via cron every 1 minute.
set -euo pipefail

# ── Variables ─────────────────────────────────────────────────────────────────
AWS_REGION="${AWS_REGION:-ap-south-1}"
NAMESPACE="P2PTrading/Containers"
METRIC_NAME="ContainerHealth"
CONTAINERS=(
  redis
  onix-bap
  onix-bpp
  onix-utilitybpp
  sandbox-bap
  sandbox-bpp
  sandbox-utilitybpp
)

# ── Publish Metrics ───────────────────────────────────────────────────────────
for container in "${CONTAINERS[@]}"; do
  status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "missing")

  if [[ "$status" == "healthy" ]]; then
    value=1
  else
    value=0
    echo "[monitor] UNHEALTHY: $container (status: $status)"
  fi

  aws cloudwatch put-metric-data \
    --region "$AWS_REGION" \
    --namespace "$NAMESPACE" \
    --metric-name "$METRIC_NAME" \
    --dimensions "ContainerName=${container}" \
    --value "$value" \
    --unit Count \
    2>/dev/null || echo "[monitor] WARNING: failed to publish metric for $container"
done
