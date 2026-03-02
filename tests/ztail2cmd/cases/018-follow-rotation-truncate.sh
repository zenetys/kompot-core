#!/bin/bash
# Test: Follow mode - rotation by truncate (copytruncate)

TEST_DIR="$WORK_DIR/018"
mkdir -p "$TEST_DIR"

LOG="$TEST_DIR/test.log"
STATE="$TEST_DIR/state"
OUT="$TEST_DIR/stdout"
ERR="$TEST_DIR/stderr"

# Create initial file with several lines
echo -e "old1\nold2\nold3\nold4" > "$LOG"

# Start follow mode in background
"$ZTAIL_SCRIPT" -f -i 1 -s "$STATE" "$LOG" -- cat > "$OUT" 2>"$ERR" &
PID=$!

sleep 0.2

# Simulate copytruncate: truncate file and write less data
echo "new1" > "$LOG"
sleep 1.2

kill $PID 2>/dev/null
wait $PID 2>/dev/null

echo "=== output ==="
cat "$OUT"
echo "=== rotation detected ==="
grep -q 'file truncated' "$ERR" && echo "yes" || echo "no"
