#!/bin/bash
# Test: Follow mode - delete and recreate empty, then append
# This is the bug scenario: delete + touch should NOT loop forever

TEST_DIR="$WORK_DIR/020"
mkdir -p "$TEST_DIR"

LOG="$TEST_DIR/test.log"
STATE="$TEST_DIR/state"
OUT="$TEST_DIR/stdout"
ERR="$TEST_DIR/stderr"

# Create initial file
echo "initial" > "$LOG"

# Start follow mode in background
"$ZTAIL_SCRIPT" -f -i 1 -s "$STATE" "$LOG" -- cat > "$OUT" 2>"$ERR" &
PID=$!

sleep 0.2

# Delete and recreate empty (touch)
rm "$LOG"
sleep 0.2
touch "$LOG"
sleep 0.5

# Now append data to the empty file
echo "after_touch" >> "$LOG"
sleep 1.2

kill $PID 2>/dev/null
wait $PID 2>/dev/null

echo "=== output ==="
cat "$OUT"
echo "=== rotation detected ==="
grep -q 'Rotation detected' "$ERR" && echo "yes" || echo "no"
