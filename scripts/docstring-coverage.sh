#!/bin/bash
#
# Generate docstring coverage report.
#
# Usage:
#   ./scripts/docstring-coverage.sh
#
# Output:
#   - Summary to terminal
#   - Full report to output/reports/docstring-coverage.txt
#   - Badge SVG to .githooks/badges/docstring-coverage.svg

set -e

REPORT_DIR="output/reports"
BADGE_DIR=".githooks/badges"
mkdir -p "$REPORT_DIR" "$BADGE_DIR"

echo "=== Docstring Coverage ==="
pipenv run interrogate src/jammy/ -v | tee "$REPORT_DIR/docstring-coverage.txt"

# Generate badge
COV_PCT=$(grep "TOTAL" "$REPORT_DIR/docstring-coverage.txt" | awk '{print $NF}' | tr -d '%')
if [ -n "$COV_PCT" ]; then
    curl -s "https://img.shields.io/badge/docstring%20coverage-${COV_PCT}%25-brightgreen" \
        -o "$BADGE_DIR/docstring-coverage.svg" 2>/dev/null || true
    echo ""
    echo "Badge: $BADGE_DIR/docstring-coverage.svg"
fi

echo "Report: $REPORT_DIR/docstring-coverage.txt"
