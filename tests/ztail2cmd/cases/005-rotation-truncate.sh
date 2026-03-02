#!/bin/bash
# Test: Log rotation by truncate (copytruncate style)

TEST_DIR="$WORK_DIR/005"
mkdir -p "$TEST_DIR"

# Create initial file with some content
echo -e "old1\nold2\nold3\nold4\nold5" > "$TEST_DIR/test.log"

# First run
echo "=== First run ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat 2>&1

# Simulate copytruncate: truncate and write less data
echo -e "new1" > "$TEST_DIR/test.log"

# Second run - should detect truncation and read from start
echo "=== After truncate ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat 2>&1 | grep -v '^\[ztail\]'
