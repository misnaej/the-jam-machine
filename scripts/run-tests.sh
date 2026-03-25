#!/bin/bash
#
# Run tests with coverage and generate badges.
#
# Usage:
#   ./scripts/run-tests.sh           # run all tests
#   ./scripts/run-tests.sh test/embedding/  # run specific tests
#
# Output:
#   - Test results to terminal + .githooks/logs/test-<timestamp>.log
#   - Coverage report to terminal
#   - Badge SVGs to .githooks/badges/
#
# This script can be called manually, by /check, or by a CI workflow.

set -e

TEST_PATH="${1:-test/}"

# --- Setup logging ---
LOG_DIR=".githooks/logs"
BADGE_DIR=".githooks/badges"
mkdir -p "$LOG_DIR" "$BADGE_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/test-$TIMESTAMP.log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Test run: $(date) ==="
echo "Test path: $TEST_PATH"
echo ""

# --- Run tests with coverage ---
FAILED=0
TEST_OUTPUT=$(pipenv run pytest "$TEST_PATH" -v --tb=short --cov=jammy --cov-report=term-missing 2>&1)
TEST_EXIT=$?
echo "$TEST_OUTPUT"

if [ "$TEST_EXIT" -eq 0 ]; then
    echo ""
    echo "✓ All tests passed"

    # Extract coverage percentage from the output (no second run)
    COV_PCT=$(echo "$TEST_OUTPUT" | grep "^TOTAL" | awk '{print $NF}' | tr -d '%')

    # Generate test passing badge
    curl -s "https://img.shields.io/badge/tests-passing-brightgreen" -o "$BADGE_DIR/tests.svg" 2>/dev/null || true

    # Generate coverage badge
    if [ -n "$COV_PCT" ]; then
        if [ "$COV_PCT" -ge 80 ]; then
            COLOR="brightgreen"
        elif [ "$COV_PCT" -ge 60 ]; then
            COLOR="yellow"
        else
            COLOR="red"
        fi
        curl -s "https://img.shields.io/badge/coverage-${COV_PCT}%25-${COLOR}" -o "$BADGE_DIR/coverage.svg" 2>/dev/null || true
        echo "Coverage: ${COV_PCT}%"
    fi
else
    FAILED=1
    curl -s "https://img.shields.io/badge/tests-failing-red" -o "$BADGE_DIR/tests.svg" 2>/dev/null || true
fi

echo ""
echo "Log: $LOG_FILE"
echo "Badges: $BADGE_DIR/tests.svg, $BADGE_DIR/coverage.svg"

exit $FAILED
