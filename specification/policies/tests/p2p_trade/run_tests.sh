#!/usr/bin/env bash
# Tests for deg.contracts.p2p_trade policy
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
POLICY_DIR="$(cd "$DIR/../.." && pwd)"
POLICY="$POLICY_DIR/p2p_trade.rego"
DATA="$DIR/test_data.json"
INPUT="$DIR/test_input.json"

PASS=0
FAIL=0

run_test() {
  local name="$1" query="$2" expected="$3"
  result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT" "$query" --format raw 2>&1) || true
  # Trim whitespace
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

echo "=== P2P Trade Policy Tests ==="
echo "--- Input: 19.5 kWh delivered (contracted 20.0), within window ---"

# delivery_in_window: window is 2020-2030, so current time is inside
run_test "delivery_in_window" \
  "data.deg.contracts.p2p_trade.delivery_in_window" \
  "true"

# delivery_quantity_compliant: 19.5 is within 10% of 20 (18-22 range)
run_test "delivery_quantity_compliant" \
  "data.deg.contracts.p2p_trade.delivery_quantity_compliant" \
  "true"

# delivery_compliant: both window and quantity pass
run_test "delivery_compliant" \
  "data.deg.contracts.p2p_trade.delivery_compliant" \
  "true"

# deviation_penalty: 0 because quantity is compliant
run_test "deviation_penalty (compliant)" \
  "data.deg.contracts.p2p_trade.deviation_penalty" \
  "0"

# sanctioned_load_check: requesting 20 from METER-001 (sanctioned 50) — OK
run_test "sanctioned_load_check (within limit)" \
  "data.deg.contracts.p2p_trade.sanctioned_load_check" \
  "true"

# settlement_amount: (19.5 * 4.50) + 5.00 = 92.75
run_test "settlement_amount" \
  "data.deg.contracts.p2p_trade.settlement_amount" \
  "92.75"

echo ""
echo "--- Testing with non-compliant delivery (15.0 kWh, below 10% tolerance) ---"

# Override input for non-compliant scenario
INPUT_NONCOMPLIANT=$(mktemp)
cat > "$INPUT_NONCOMPLIANT" <<'EOF'
{
  "deliveredQuantity": 15.0,
  "meterId": "METER-002",
  "requestedQuantity": 20.0
}
EOF

result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_NONCOMPLIANT" \
  "data.deg.contracts.p2p_trade.deviation_penalty" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
expected="10"
if [ "$result" = "$expected" ]; then
  echo "  PASS: deviation_penalty (non-compliant: 5 kWh short * 2.00/kWh = 10)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: deviation_penalty (non-compliant)"
  echo "    expected: $expected"
  echo "    got:      $result"
  FAIL=$((FAIL + 1))
fi

# sanctioned_load_check should fail: requesting 20 from METER-002 (sanctioned 10)
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_NONCOMPLIANT" \
  "data.deg.contracts.p2p_trade.sanctioned_load_check" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "" ] || [ "$result" = "undefined" ]; then
  echo "  PASS: sanctioned_load_check (exceeds limit — undefined/blocked)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: sanctioned_load_check (should be undefined when exceeding limit)"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

rm -f "$INPUT_NONCOMPLIANT"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
