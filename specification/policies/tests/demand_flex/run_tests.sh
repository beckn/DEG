#!/usr/bin/env bash
# Tests for deg.contracts.demand_flex policy
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
POLICY_DIR="$(cd "$DIR/../.." && pwd)"
POLICY="$POLICY_DIR/demand_flex.rego"
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

echo "=== Demand Flexibility Policy Tests ==="
echo "--- Input: freq=49.2, spotPrice=12, signal=ACTIVE, baseline=200, actual=100 ---"
echo "--- Data: threshold=10, maxEvents=5, capacity=100, incentiveRate=3.50, 2 prior events ---"

# demand_response_triggered: freq 49.2 < 49.5 → true
run_test "demand_response_triggered (low frequency)" \
  "data.deg.contracts.demand_flex.demand_response_triggered" \
  "true"

# events_exhausted: 2 events < 5 max → should be undefined (not exhausted)
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT" \
  "data.deg.contracts.demand_flex.events_exhausted" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ -z "$result" ] || [ "$result" = "undefined" ]; then
  echo "  PASS: events_exhausted (2 of 5 — not exhausted)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: events_exhausted (should be undefined)"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

# event_allowed: triggered + not exhausted → true
run_test "event_allowed" \
  "data.deg.contracts.demand_flex.event_allowed" \
  "true"

# actual_curtailment: 200 - 100 = 100
run_test "actual_curtailment" \
  "data.deg.contracts.demand_flex.actual_curtailment" \
  "100"

# curtailment_compliant: 100 >= 100 * 0.8 (80) → true
run_test "curtailment_compliant" \
  "data.deg.contracts.demand_flex.curtailment_compliant" \
  "true"

# incentive_amount: 100 kW * 3.50 INR/kW * 1 hour = 350
# hours = (4600000000000 - 1000000000000) / 3600000000000 = 1.0
run_test "incentive_amount" \
  "data.deg.contracts.demand_flex.incentive_amount" \
  "350"

echo ""
echo "--- Testing exhausted events (5 of 5) ---"

DATA_EXHAUSTED=$(mktemp)
cat > "$DATA_EXHAUSTED" <<'EOF'
{
  "contract": {
    "inputs": {
      "priceThreshold": 10.0,
      "maxEventsPerMonth": 5,
      "curtailmentCapacity": 100.0,
      "incentiveRate": 3.50
    }
  },
  "events_this_month": [
    {"eventId":"1"},{"eventId":"2"},{"eventId":"3"},{"eventId":"4"},{"eventId":"5"}
  ]
}
EOF

result=$(opa eval -d "$POLICY" -d "$DATA_EXHAUSTED" -i "$INPUT" \
  "data.deg.contracts.demand_flex.events_exhausted" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "true" ]; then
  echo "  PASS: events_exhausted (5 of 5)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: events_exhausted"
  echo "    expected: true"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

# event_allowed should be undefined when exhausted
result=$(opa eval -d "$POLICY" -d "$DATA_EXHAUSTED" -i "$INPUT" \
  "data.deg.contracts.demand_flex.event_allowed" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ -z "$result" ] || [ "$result" = "undefined" ]; then
  echo "  PASS: event_allowed (blocked — events exhausted)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: event_allowed (should be undefined when exhausted)"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

rm -f "$DATA_EXHAUSTED"

echo ""
echo "--- Testing non-compliant curtailment ---"

INPUT_LOW_CURTAIL=$(mktemp)
cat > "$INPUT_LOW_CURTAIL" <<'EOF'
{
  "gridFrequency": 49.2,
  "spotPrice": 12.0,
  "curtailmentSignal": "ACTIVE",
  "baselineLoad": 200.0,
  "actualLoad": 170.0,
  "eventStartNs": 1000000000000,
  "eventEndNs":   4600000000000
}
EOF

# actual_curtailment: 200 - 170 = 30 (below 80% of 100 = 80)
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_LOW_CURTAIL" \
  "data.deg.contracts.demand_flex.actual_curtailment" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "30" ]; then
  echo "  PASS: actual_curtailment (low: 30 kW)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: actual_curtailment (low)"
  echo "    expected: 30"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

# incentive_amount: 0 when not compliant
result=$(opa eval -d "$POLICY" -d "$DATA" -i "$INPUT_LOW_CURTAIL" \
  "data.deg.contracts.demand_flex.incentive_amount" --format raw 2>&1) || true
result=$(echo "$result" | tr -d '[:space:]')
if [ "$result" = "0" ]; then
  echo "  PASS: incentive_amount (non-compliant = 0)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: incentive_amount (non-compliant)"
  echo "    expected: 0"
  echo "    got: $result"
  FAIL=$((FAIL + 1))
fi

rm -f "$INPUT_LOW_CURTAIL"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
