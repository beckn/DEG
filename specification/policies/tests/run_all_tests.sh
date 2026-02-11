#!/usr/bin/env bash
# Run all DEG policy tests
set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

TOTAL_PASS=0
TOTAL_FAIL=0
SUITES=0
SUITE_FAILURES=0

for suite_dir in "$DIR"/*/; do
  script="$suite_dir/run_tests.sh"
  [ -f "$script" ] || continue
  SUITES=$((SUITES + 1))
  echo ""
  echo "================================================================"
  if bash "$script"; then
    TOTAL_PASS=$((TOTAL_PASS + 1))
  else
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    SUITE_FAILURES=$((SUITE_FAILURES + 1))
  fi
  echo "================================================================"
done

echo ""
echo "==============================="
echo " ALL SUITES: $SUITES run, $SUITE_FAILURES failed"
echo "==============================="

[ "$SUITE_FAILURES" -eq 0 ]
