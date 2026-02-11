#!/usr/bin/env bash
# Tests for deg.revenue policy (multi-party net-zero revenue model)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
POLICY_DIR="$(cd "$DIR/../.." && pwd)"
POLICY="$POLICY_DIR/revenue.rego"
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

echo "=== Revenue Model Policy Tests ==="
echo "--- Input: 19.5 kWh delivered (contracted 20), price=4.50, wheeling=0.25 ---"
echo "--- 4 roles: buyer, seller, source_utility, platform ---"

# flow_amount: energy_payment = 19.5 * 4.50 = 87.75
run_test "flow_amount[energy_payment]" \
  "data.deg.revenue.flow_amount.energy_payment" \
  "87.75"

# flow_amount: wheeling_charge = 19.5 * 0.25 = 4.875
run_test "flow_amount[wheeling_charge]" \
  "data.deg.revenue.flow_amount.wheeling_charge" \
  "4.875"

# flow_amount: platform_fee_buyer = 87.75 * 0.01 = 0.8775
run_test "flow_amount[platform_fee_buyer]" \
  "data.deg.revenue.flow_amount.platform_fee_buyer" \
  "0.8775"

# flow_amount: platform_fee_seller = 87.75 * 0.01 = 0.8775
run_test "flow_amount[platform_fee_seller]" \
  "data.deg.revenue.flow_amount.platform_fee_seller" \
  "0.8775"

# flow_amount: deviation_penalty = (20 - 19.5) * 2.00 = 1.0
run_test "flow_amount[deviation_penalty]" \
  "data.deg.revenue.flow_amount.deviation_penalty" \
  "1"

# net_zero_valid: all flows must sum to zero
run_test "net_zero_valid" \
  "data.deg.revenue.net_zero_valid" \
  "true"

# net_position: buyer pays (negative)
# outflows: energy(87.75) + wheeling(4.875) + platform_fee_buyer(0.8775) = 93.5025
# inflows: deviation_penalty(1.0) = 1.0
# net = 1.0 - 93.5025 = -92.5025
run_test "net_position[buyer]" \
  "data.deg.revenue.net_position.buyer" \
  "-92.5025"

# net_position: seller receives
# inflows: energy(87.75) = 87.75
# outflows: platform_fee_seller(0.8775) + deviation_penalty(1.0) = 1.8775
# net = 87.75 - 1.8775 = 85.8725
run_test "net_position[seller]" \
  "data.deg.revenue.net_position.seller" \
  "85.8725"

# net_position: source_utility receives
# inflows: wheeling(4.875)
# outflows: 0
# net = 4.875
run_test "net_position[source_utility]" \
  "data.deg.revenue.net_position.source_utility" \
  "4.875"

# net_position: platform receives
# inflows: platform_fee_buyer(0.8775) + platform_fee_seller(0.8775) = 1.755
# outflows: 0
# net = 1.755
run_test "net_position[platform]" \
  "data.deg.revenue.net_position.platform" \
  "1.755"

echo ""
echo "--- Testing full delivery (no penalty) ---"

INPUT_FULL=$(mktemp)
cat > "$INPUT_FULL" <<'EOF'
{
  "deliveredKwh": 20.0,
  "pricePerKwh": 4.50,
  "wheelingRatePerKwh": 0.25,
  "deviationPenaltyPerKwh": 2.00
}
EOF

result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_FULL" \
  "data.deg.revenue.flow_amount.deviation_penalty" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "0" ]; then
  echo "  PASS: deviation_penalty (full delivery = 0)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: deviation_penalty (full delivery)"
  echo "    expected: 0"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_FULL" \
  "data.deg.revenue.net_zero_valid" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "true" ]; then
  echo "  PASS: net_zero_valid (full delivery)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: net_zero_valid (full delivery)"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

rm -f "$INPUT_FULL"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
