#!/bin/bash
# Phase 1 Diagnostic Script - E2E Test Debugging
# Run this script to diagnose failing tests

set -e

echo "=========================================="
echo "Phase 1: E2E Test Diagnostic Script"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Run failing tests with maximum verbosity"
echo "2. Capture full output and errors"
echo "3. Run full E2E suite for baseline"
echo "4. Save results to file"
echo ""

cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Create results directory
mkdir -p /tmp/phase1_diagnostics
RESULTS_DIR="/tmp/phase1_diagnostics"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "1. Diagnosing test_barge_in_during_tts..."
echo "=========================================="
python3 -m pytest tests/integration/test_voice_e2e.py::test_barge_in_during_tts -vvvs \
    2>&1 | tee "$RESULTS_DIR/barge_in_diagnostic_$TIMESTAMP.txt"

echo ""
echo "2. Diagnosing test_error_handling..."
echo "=========================================="
python3 -m pytest tests/integration/test_voice_e2e.py::test_error_handling -vvvs \
    2>&1 | tee "$RESULTS_DIR/error_handling_diagnostic_$TIMESTAMP.txt"

echo ""
echo "3. Running full E2E suite for baseline..."
echo "=========================================="
python3 -m pytest tests/integration/test_voice_e2e.py -v \
    2>&1 | tee "$RESULTS_DIR/e2e_baseline_$TIMESTAMP.txt"

echo ""
echo "4. Generating summary..."
echo "=========================================="
echo "Diagnostic sessions saved to: $RESULTS_DIR"
echo ""
echo "Files generated:"
echo "  - $RESULTS_DIR/barge_in_diagnostic_$TIMESTAMP.txt"
echo "  - $RESULTS_DIR/error_handling_diagnostic_$TIMESTAMP.txt"
echo "  - $RESULTS_DIR/e2e_baseline_$TIMESTAMP.txt"
echo ""
echo "Next steps:"
echo "  1. Review diagnostic files"
echo "  2. Identify root causes"
echo "  3. Apply fixes"
echo "  4. Re-run tests to verify"
echo ""
echo "To view results:"
echo "  cat $RESULTS_DIR/barge_in_diagnostic_$TIMESTAMP.txt"
echo "  cat $RESULTS_DIR/error_handling_diagnostic_$TIMESTAMP.txt"
echo "  cat $RESULTS_DIR/e2e_baseline_$TIMESTAMP.txt"