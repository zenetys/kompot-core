#!/bin/bash
# Test: Multiple consecutive runs with incremental data

TEST_DIR="$WORK_DIR/012"
mkdir -p "$TEST_DIR"

# Start fresh
echo "a" > "$TEST_DIR/test.log"

echo "=== Run 1 ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat

echo "b" >> "$TEST_DIR/test.log"
echo "=== Run 2 ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat

echo "c" >> "$TEST_DIR/test.log"
echo "=== Run 3 ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat

echo "=== Run 4 (no change) ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat
echo "(end)"
