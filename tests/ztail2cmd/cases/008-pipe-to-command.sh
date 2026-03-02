#!/bin/bash
# Test: Pipe output to a command with arguments

TEST_DIR="$WORK_DIR/008"
mkdir -p "$TEST_DIR"

# Create test file
echo -e "apple\nbanana\napricot\ncherry" > "$TEST_DIR/test.log"

# Pipe to grep (filter lines starting with 'a')
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- grep '^a'
