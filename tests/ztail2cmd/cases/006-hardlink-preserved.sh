#!/bin/bash
# Test: Hardlink preserves access to rotated file

TEST_DIR="$WORK_DIR/006"
mkdir -p "$TEST_DIR"

# Create initial file
echo -e "line1\nline2" > "$TEST_DIR/test.log"

# First run - creates hardlink
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat >/dev/null

# Check hardlink was created
hardlink_count=$(find "$TEST_DIR" -name '.ztail_*' | wc -l)
echo "hardlinks_after_first_run: $hardlink_count"

# Append data
echo "line3" >> "$TEST_DIR/test.log"

# Simulate rotation
mv "$TEST_DIR/test.log" "$TEST_DIR/test.log.1"
echo "new_content" > "$TEST_DIR/test.log"

# Second run - should finish old file via hardlink then read new
"$ZTAIL_SCRIPT" -s "$TEST_DIR/state" "$TEST_DIR/test.log" -- cat 2>&1 | grep -v '^\[ztail\]'

# After rotation handling, old hardlink should be removed
hardlink_count=$(find "$TEST_DIR" -name '.ztail_*' | wc -l)
echo "hardlinks_after_rotation: $hardlink_count"
