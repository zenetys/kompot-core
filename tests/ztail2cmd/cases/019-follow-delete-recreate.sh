#!/bin/bash
# Test: Follow mode - delete file and recreate with data

TEST_DIR="$WORK_DIR/019"
mkdir -p "$TEST_DIR"

LOG="$TEST_DIR/test.log"
STATE="$TEST_DIR/state"
OUT="$TEST_DIR/stdout"
ERR="$TEST_DIR/stderr"

# Create initial file
echo -e "old1\nold2" > "$LOG"

# Start follow mode in background
"$ZTAIL_SCRIPT" -f -i 1 -s "$STATE" "$LOG" -- cat > "$OUT" 2>"$ERR" &
PID=$!

sleep 0.2

# Delete and recreate with new content
rm "$LOG"
sleep 0.2
echo -e "new1\nnew2" > "$LOG"
sleep 1.2

kill $PID 2>/dev/null
wait $PID 2>/dev/null

echo "=== output ==="
cat "$OUT"
echo "=== rotation detected ==="
grep -q 'Rotation detected' "$ERR" && echo "yes" || echo "no"
