#!/bin/bash
# Test: State file format verification

TEST_DIR="$WORK_DIR/014"
mkdir -p "$TEST_DIR"

# Create test file
echo -e "12345\n67890" > "$TEST_DIR/test.log"

# Run
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat >/dev/null

# Verify state file format
echo "=== State file content ==="
echo "line_count: $(wc -l < "$TEST_DIR/state")"
echo "inode_is_number: $(head -1 "$TEST_DIR/state" | grep -qE '^[0-9]+$' && echo yes || echo no)"
echo "offset_is_number: $(sed -n 2p "$TEST_DIR/state" | grep -qE '^[0-9]+$' && echo yes || echo no)"
echo "offset_value: $(sed -n 2p "$TEST_DIR/state")"
