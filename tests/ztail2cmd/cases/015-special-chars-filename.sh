#!/bin/bash
# Test: Filename with spaces and special characters

TEST_DIR="$WORK_DIR/015"
mkdir -p "$TEST_DIR"

# Create file with spaces in name
echo "content" > "$TEST_DIR/my log file.log"

# Run
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/my log file.log" -- cat

echo "---"
echo "success: yes"
