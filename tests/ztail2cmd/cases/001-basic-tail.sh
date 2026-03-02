#!/bin/bash
# Test: Basic tail - first run reads entire file

TEST_DIR="$WORK_DIR/001"
mkdir -p "$TEST_DIR"

# Create test file
echo -e "line1\nline2\nline3" > "$TEST_DIR/test.log"

# Run ztail2cmd
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat

echo "---"
echo "state_exists: $(test -f "$TEST_DIR/state" && echo yes || echo no)"
