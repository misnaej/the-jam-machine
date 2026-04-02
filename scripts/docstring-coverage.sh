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

# Single interrogate run: verbose report + badge + threshold check
pipenv run interrogate src/jammy/ -v \
    --fail-under "$FAIL_UNDER" \
    --generate-badge "$BADGE_DIR/docstring-coverage.svg" \
    | tee "$REPORT_DIR/docstring-coverage.txt"
