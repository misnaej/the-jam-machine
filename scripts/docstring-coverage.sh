#!/bin/bash
#
# Generate docstring coverage report and badge.
#
# Usage:
#   ./scripts/docstring-coverage.sh
#
# Output:
#   - Summary to terminal
#   - Full report to output/reports/docstring-coverage.txt
#   - Badge SVG to .githooks/badges/docstring-coverage.svg
#
# Exits with code 1 if coverage is below 95%.

set -e

REPORT_DIR="output/reports"
BADGE_DIR=".githooks/badges"
FAIL_UNDER=95

mkdir -p "$REPORT_DIR" "$BADGE_DIR"

# Generate report
pipenv run interrogate src/jammy/ -v | tee "$REPORT_DIR/docstring-coverage.txt"

# Generate badge
pipenv run interrogate src/jammy/ --generate-badge "$BADGE_DIR/docstring-coverage.svg" -q 2>/dev/null || true

# Check threshold
if ! pipenv run interrogate src/jammy/ --fail-under "$FAIL_UNDER" -q 2>/dev/null; then
    echo ""
    echo "ERROR: Docstring coverage below ${FAIL_UNDER}%."
    grep "MISS" "$REPORT_DIR/docstring-coverage.txt" || true
    exit 1
fi
