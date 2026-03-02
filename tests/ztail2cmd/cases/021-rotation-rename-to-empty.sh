#!/bin/bash
# Test: Single run - rotation to empty file then append
# Validates that inode is persisted even when new file is empty

TEST_DIR="$WORK_DIR/021"
mkdir -p "$TEST_DIR"

LOG="$TEST_DIR/test.log"
STATE="$TEST_DIR/state"

# Create initial file
echo -e "old1\nold2" > "$LOG"

# First run
echo "=== First run ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat

# Save old inode
OLD_INODE=$(sed -n '1p' "$STATE")

# Rotate to empty file
mv "$LOG" "$LOG.1"
touch "$LOG"

# Second run - should detect rotation but no data
echo "=== After rotation to empty ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat 2>&1 | grep -v '^\[ztail\]'
echo "(end)"

# Verify state has new inode (not stuck on old one)
NEW_INODE=$(sed -n '1p' "$STATE")
if [[ "$OLD_INODE" != "$NEW_INODE" ]]; then
    echo "inode_updated: yes"
else
    echo "inode_updated: no (BUG)"
fi

# Third run - should NOT re-detect rotation
echo "=== Third run (no re-detect) ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat 2>&1
echo "(end)"

# Append data and run again
echo "new_data" >> "$LOG"
echo "=== After append ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat
