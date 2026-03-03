#!/bin/bash
# Test: AND mode - all members OK entire period
# Period: 0-1000
#
# Both sql and www are OK for the entire period
# Result: 100% available

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=AND
0	sql	OK
0	www	OK
EOF
# ASSERT: 1000	0	0	100.0000
