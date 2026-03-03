#!/bin/bash
# Test: Host UNREACHABLE = Unknown (regardless of service state)
# Period: 0-1000

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UNREACHABLE	OK
EOF
# ASSERT: 0	0	1000	100.0000
