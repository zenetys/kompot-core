#!/bin/bash
# Test: Log rotation by rename (inode change)

TEST_DIR="$WORK_DIR/004"
mkdir -p "$TEST_DIR"

# Create initial file
echo -e "old1\nold2" > "$TEST_DIR/test.log"

# First run
echo "=== First run ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat 2>&1

# Simulate rotation: rename old, create new
mv "$TEST_DIR/test.log" "$TEST_DIR/test.log.1"
echo -e "new1\nnew2" > "$TEST_DIR/test.log"

# Second run - should detect rotation and read new file from start
echo "=== After rotation ==="
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat 2>&1 | grep -v '^\[ztail\]'
