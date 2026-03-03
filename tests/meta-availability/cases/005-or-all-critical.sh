#!/bin/bash
# Test: OR mode - all members CRITICAL entire period
# Period: 0-1000
#
# Both sql and www are CRITICAL for the entire period
# OR mode still returns 0% because no one is available
# Result: 0% available

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=OR
0	sql	CRITICAL
0	www	CRITICAL
EOF
# ASSERT: 0	1000	0	0.0000
