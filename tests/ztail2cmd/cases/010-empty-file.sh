#!/bin/bash
# Test: Empty file handling

TEST_DIR="$WORK_DIR/010"
mkdir -p "$TEST_DIR"

# Create empty file
touch "$TEST_DIR/test.log"

# First run on empty file
echo "=== Empty file ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat
echo "(end of empty)"

# Append data
echo "data" >> "$TEST_DIR/test.log"

# Second run
echo "=== After append ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat
