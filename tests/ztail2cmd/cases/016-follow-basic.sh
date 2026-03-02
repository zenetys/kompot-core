#!/bin/bash
# Test: Follow mode - basic append detection

TEST_DIR="$WORK_DIR/016"
mkdir -p "$TEST_DIR"

LOG="$TEST_DIR/test.log"
STATE="$TEST_DIR/state"
OUT="$TEST_DIR/stdout"
ERR="$TEST_DIR/stderr"

# Create initial file
echo "line1" > "$LOG"

# Start follow mode in background
"$ZTAIL_SCRIPT" -f -i 1 -s "$STATE" "$LOG" -- cat > "$OUT" 2>"$ERR" &
PID=$!

sleep 0.2

# Append first wave
echo "line2" >> "$LOG"
sleep 0.2

# Append second wave
echo -e "line3\nline4" >> "$LOG"
sleep 1.2

kill $PID 2>/dev/null
wait $PID 2>/dev/null

echo "=== output ==="
cat "$OUT"
