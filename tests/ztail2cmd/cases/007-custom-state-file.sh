#!/bin/bash
# Test: Custom state file path with -s option

TEST_DIR="$WORK_DIR/007"
mkdir -p "$TEST_DIR/data" "$TEST_DIR/state"

# Create test file
echo -e "line1\nline2" > "$TEST_DIR/data/test.log"

# Run with custom state file location
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state/mystate" "$TEST_DIR/data/test.log" -- cat

echo "---"
echo "state_in_custom_location: $(test -f "$TEST_DIR/state/mystate" && echo yes || echo no)"
echo "state_next_to_log: $(test -f "$TEST_DIR/data/test.log.ztail" && echo no || echo yes)"
