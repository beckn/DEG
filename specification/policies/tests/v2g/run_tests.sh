#!/usr/bin/env bash
# Tests for deg.contracts.v2g policy
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
POLICY_DIR="$(cd "$DIR/../.." && pwd)"
POLICY="$POLICY_DIR/v2g.rego"
DATA="$DIR/test_data.json"
INPUT="$DIR/test_input.json"

PASS=0
FAIL=0

run_test() {
  local name="$1" query="$2" expected="$3"
  result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT" "$query" --format raw 2>&1) || true
  result=$(echo "$result" | tr -d '[:space:]')
  expected_trimmed=$(echo "$expected" | tr -d '[:space:]')
  if [ "$result" = "$expected_trimmed" ]; then
    echo "  PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $name"
    echo "    expected: $expected"
    echo "    got:      $result"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== V2G Policy Tests ==="
echo "--- Input: battery=80%, 60kWh cap, v2g=true, gridStress=true ---"
echo "--- Data: minCharge=20%, chargingRate=8, v2gRate=12 ---"

# v2g_eligible: battery 80% > 20% min, v2gCapable=true, charger supports
run_test "v2g_eligible" \
  "data.deg.contracts.v2g.v2g_eligible" \
  "true"

# should_discharge: eligible + gridStress=true
run_test "should_discharge" \
  "data.deg.contracts.v2g.should_discharge" \
  "true"

# max_discharge_kwh: current = 60 * (80/100) = 48, min = 60 * (20/100) = 12, diff = 36
run_test "max_discharge_kwh" \
  "data.deg.contracts.v2g.max_discharge_kwh" \
  "36"

# net_payment: (30 * 8) - (10 * 12) = 240 - 120 = 120 (owner pays net)
run_test "net_payment" \
  "data.deg.contracts.v2g.net_payment" \
  "120"

echo ""
echo "--- Testing V2G ineligible (low battery) ---"

INPUT_LOW=$(mktemp)
cat > "$INPUT_LOW" <<'EOF'
{
  "vehicleBatteryPct": 15,
  "vehicleBatteryKwh": 60,
  "v2gCapable": true,
  "gridStress": true,
  "totalChargedKwh": 5.0,
  "totalDischargedKwh": 20.0
}
EOF

# v2g_eligible: 15% < 20% min → undefined
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_LOW" \
  "data.deg.contracts.v2g.v2g_eligible" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ -z "$result" ] || [ "$result" = "undefined" ]; then
  echo "  PASS: v2g_eligible (low battery — ineligible)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: v2g_eligible (should be undefined for low battery)"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

# should_discharge: not eligible → undefined
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_LOW" \
  "data.deg.contracts.v2g.should_discharge" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ -z "$result" ] || [ "$result" = "undefined" ]; then
  echo "  PASS: should_discharge (ineligible — blocked)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: should_discharge (should be undefined)"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

# max_discharge_kwh: current=9, min=12 → 0 (can't discharge)
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_LOW" \
  "data.deg.contracts.v2g.max_discharge_kwh" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "0" ]; then
  echo "  PASS: max_discharge_kwh (below min charge = 0)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: max_discharge_kwh (below min)"
  echo "    expected: 0"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

# net_payment: (5 * 8) - (20 * 12) = 40 - 240 = -200 (owner receives money)
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_LOW" \
  "data.deg.contracts.v2g.net_payment" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "-200" ]; then
  echo "  PASS: net_payment (owner earns: -200)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: net_payment (owner earns)"
  echo "    expected: -200"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

rm -f "$INPUT_LOW"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
