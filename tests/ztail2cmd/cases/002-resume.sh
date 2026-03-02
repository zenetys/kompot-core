#!/bin/bash
# Test: Resume from last position

TEST_DIR="$WORK_DIR/002"
mkdir -p "$TEST_DIR"

# Create initial file
echo -e "line1\nline2\nline3" > "$TEST_DIR/test.log"

# First run
echo "=== First run ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat

# Append more data
echo -e "line4\nline5" >> "$TEST_DIR/test.log"

# Second run - should only output new lines
echo "=== Second run ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat
