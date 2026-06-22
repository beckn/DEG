#!/bin/bash
# EC2 host bootstrap (cloud-init user-data). Idempotent, safe to re-run.
# Preps the host so CodeDeploy/CodePipeline can deliver + run the sandbox app:
#   - installs docker, awscli, CodeDeploy agent, CloudWatch agent
#   - clones the PUBLIC DEG repo (compose + onix configs + scripts); updated MANUALLY
#   - the SANDBOX app and its deploy (fetch-secrets, docker compose up) arrive via
#     CodeDeploy (appspec.yml hooks) — NOT here, and there are NO SSH deploy keys.
set -euxo pipefail

AWS_REGION="ap-south-1"
APP_ENV="uat"
APP_PATH="/opt/app"
DEG_REPO="https://github.com/beckn/DEG.git"   # public — cloned over HTTPS, no key
DEG_BRANCH="p2p-trading"
INSTALL_RELATIVE="testnet/p2p-trading-interdiscom-devkit/install"
INSTALL_PATH="${APP_PATH}/deg/${INSTALL_RELATIVE}"
SECRET_PREFIX="p2p-trading/${APP_ENV}"
CW_AGENT_SSM_PARAM="/${SECRET_PREFIX}/cloudwatch-agent-config"
export AWS_REGION APP_ENV INSTALL_PATH

exec > >(tee -a /var/log/bootstrap.log) 2>&1
echo "=== Bootstrap started: $(date) ==="

# ── System dependencies ───────────────────────────────────────────────────────
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
# NOTE: no 'awscli' here — that apt package was removed in Ubuntu 24.04; we install AWS CLI v2 below.
apt-get install -y docker.io jq git curl wget ruby-full netcat-openbsd python3 unzip

# AWS CLI v2 (official installer — apt 'awscli' is unavailable on Ubuntu 24.04)
if ! command -v aws &>/dev/null; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o /tmp/awscliv2.zip
  unzip -q /tmp/awscliv2.zip -d /tmp
  /tmp/aws/install --update
  rm -rf /tmp/aws /tmp/awscliv2.zip
fi

# Docker Compose v2 plugin
if ! docker compose version &>/dev/null; then
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

# CloudWatch agent
if ! command -v amazon-cloudwatch-agent-ctl &>/dev/null; then
  wget -q "https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb" -O /tmp/cwa.deb
  dpkg -i /tmp/cwa.deb || apt-get -f install -y
fi

# CodeDeploy agent (delivers the sandbox app)
if ! service codedeploy-agent status &>/dev/null; then
  wget -q "https://aws-codedeploy-${AWS_REGION}.s3.${AWS_REGION}.amazonaws.com/latest/install" -O /tmp/cd-install
  chmod +x /tmp/cd-install
  /tmp/cd-install auto
fi

systemctl enable docker
systemctl start docker

# Docker daemon: json-file by default (per-container awslogs is set in compose)
cat > /etc/docker/daemon.json <<'JSON'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
JSON
systemctl restart docker

# ── Clone the PUBLIC DEG repo (compose, onix configs, scripts) ─────────────────
# Updates are a MANUAL `git pull` — DEG is intentionally not in the pipeline.
mkdir -p "$APP_PATH"
if [ -d "$APP_PATH/deg/.git" ]; then
  git -C "$APP_PATH/deg" fetch origin && \
  git -C "$APP_PATH/deg" checkout "$DEG_BRANCH" && \
  git -C "$APP_PATH/deg" pull origin "$DEG_BRANCH" || echo "WARN: DEG pull failed — keeping existing checkout"
else
  git clone --branch "$DEG_BRANCH" --single-branch "$DEG_REPO" "$APP_PATH/deg"
fi

# ── CloudWatch agent config (SSM param if present, else inline default) ────────
CW_CONFIG=/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
if ! aws ssm get-parameter --region "$AWS_REGION" --name "$CW_AGENT_SSM_PARAM" --query Parameter.Value --output text > "$CW_CONFIG" 2>/dev/null; then
  cat > "$CW_CONFIG" <<'JSON'
{ "metrics": { "append_dimensions": { "InstanceId": "${aws:InstanceId}" }, "metrics_collected": {
  "mem":  { "measurement": ["mem_used_percent"],  "metrics_collection_interval": 60 },
  "disk": { "measurement": ["disk_used_percent"], "metrics_collection_interval": 60, "resources": ["/"] } } } }
JSON
fi
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c "file:${CW_CONFIG}" -s || true

# ── Container-health monitor cron (script ships in the DEG repo) ───────────────
if [ -f "${INSTALL_PATH}/scripts/monitor_containers.sh" ]; then
  chmod +x "${INSTALL_PATH}/scripts/monitor_containers.sh"
  ( crontab -l 2>/dev/null | grep -v monitor_containers.sh; \
    echo "* * * * * AWS_REGION=${AWS_REGION} /bin/bash ${INSTALL_PATH}/scripts/monitor_containers.sh >> /var/log/container-health.log 2>&1" ) | crontab -
fi

service codedeploy-agent start || systemctl start codedeploy-agent || true
echo "=== Bootstrap complete: $(date). Sandbox app deploys via CodePipeline/CodeDeploy. ==="
