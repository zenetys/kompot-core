#!/bin/bash
# Test: File not found should fail and report error

TEST_DIR="$WORK_DIR/009"
mkdir -p "$TEST_DIR"

# Try to tail non-existent file
set +e
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/nonexistent.log" -- cat 2>&1 | sed 's|/tmp/[^/]*/|/tmp/WORK/|g'
exit_code=${PIPESTATUS[0]}
set -e

echo "exit_code: $exit_code"
