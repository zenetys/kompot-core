#!/bin/bash
# Test: Single run - multiple successive rotations

TEST_DIR="$WORK_DIR/022"
mkdir -p "$TEST_DIR"

LOG="$TEST_DIR/test.log"
STATE="$TEST_DIR/state"

# Round 1: initial file
echo "round1" > "$LOG"
echo "=== Round 1 ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat

# Round 2: rotate (rename) and new content
mv "$LOG" "$LOG.1"
echo "round2" > "$LOG"
echo "=== Round 2 (after rename rotation) ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat 2>&1 | grep -v '^\[ztail\]'

# Round 3: rotate (truncate) with less data so truncation is detected
echo "r3" > "$LOG"
echo "=== Round 3 (after truncate rotation) ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat 2>&1 | grep -v '^\[ztail\]'

# Round 4: delete + recreate empty + append
rm "$LOG"
touch "$LOG"
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat 2>/dev/null
echo "round4" >> "$LOG"
echo "=== Round 4 (after delete+touch+append) ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat

# Round 5: normal append (no rotation)
echo "round5" >> "$LOG"
echo "=== Round 5 (normal append) ==="
"$ZTAIL_SCRIPT" -s "$STATE" "$LOG" -- cat
