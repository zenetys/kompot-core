#!/bin/bash
# Test: Binary data handling (null bytes, etc.)

TEST_DIR="$WORK_DIR/013"
mkdir -p "$TEST_DIR"

# Create file with some binary-ish content
printf 'line1\x00null\nline2\n' > "$TEST_DIR/test.log"

# First run
echo "=== First run ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat | od -c | head -3

# Append more
printf 'line3\n' >> "$TEST_DIR/test.log"

# Second run
echo "=== Second run ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat
