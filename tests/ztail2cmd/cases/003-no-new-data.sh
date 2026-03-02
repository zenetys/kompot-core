#!/bin/bash
# Test: No new data - should output nothing

TEST_DIR="$WORK_DIR/003"
mkdir -p "$TEST_DIR"

# Create file
echo -e "line1\nline2" > "$TEST_DIR/test.log"

# First run
echo "=== First run ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat

# Second run with no changes
echo "=== Second run (no new data) ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat
echo "(end)"
