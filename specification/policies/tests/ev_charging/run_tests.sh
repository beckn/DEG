#!/usr/bin/env bash
# Tests for deg.contracts.ev_charging policy
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
POLICY_DIR="$(cd "$DIR/../.." && pwd)"
POLICY="$POLICY_DIR/ev_charging.rego"
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

# Check if result is defined (not empty/undefined)
run_test_defined() {
  local name="$1" query="$2"
  result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT" "$query" --format raw 2>&1) || true
  result=$(echo "$result" | tr -d '[:space:]')
  if [ -n "$result" ] && [ "$result" != "undefined" ]; then
    echo "  PASS: $name = $result"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $name (undefined)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== EV Charging Policy Tests ==="
echo "--- Input: CCS2 vehicle, 50kW requested, 25 kWh delivered, charging-started ---"

# connector_compatible: CCS2 == CCS2
run_test "connector_compatible (CCS2 match)" \
  "data.deg.contracts.ev_charging.connector_compatible" \
  "true"

# power_feasible: 50 kW within [7, 60]
run_test "power_feasible" \
  "data.deg.contracts.ev_charging.power_feasible" \
  "true"

# reservation_available: supported=true, occupied=false
run_test "reservation_available" \
  "data.deg.contracts.ev_charging.reservation_available" \
  "true"

# charging_price_per_kwh: depends on current hour, just check it's defined
run_test_defined "charging_price_per_kwh (time-of-day)" \
  "data.deg.contracts.ev_charging.charging_price_per_kwh"

# total_charge: depends on time-of-day rate, check it's defined
run_test_defined "total_charge" \
  "data.deg.contracts.ev_charging.total_charge"

# cancellation_fee: fulfillmentState=charging-started → 300 * 0.30 = 90
run_test "cancellation_fee (charging started)" \
  "data.deg.contracts.ev_charging.cancellation_fee" \
  "90"

echo ""
echo "--- Testing Type2→CCS2 backward compatibility ---"

INPUT_TYPE2=$(mktemp)
cat > "$INPUT_TYPE2" <<'EOF'
{
  "vehicleConnectorType": "Type2",
  "requestedPowerKW": 22,
  "deliveredKwh": 10.0,
  "fulfillmentState": "order-initiated",
  "estimatedTotal": 100.0
}
EOF

result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_TYPE2" \
  "data.deg.contracts.ev_charging.connector_compatible" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "true" ]; then
  echo "  PASS: connector_compatible (Type2 on CCS2 — backward compat)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: connector_compatible (Type2 on CCS2)"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

# cancellation_fee: order-initiated → 0
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_TYPE2" \
  "data.deg.contracts.ev_charging.cancellation_fee" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "0" ]; then
  echo "  PASS: cancellation_fee (order-initiated = 0)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: cancellation_fee (order-initiated)"
  echo "    expected: 0"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

rm -f "$INPUT_TYPE2"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
