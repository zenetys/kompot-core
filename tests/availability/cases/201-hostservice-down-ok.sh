#!/bin/bash
# Test: Host DOWN + Service OK = UNKNOWN
# Period: 0-1000
# If host is DOWN, we cannot determine service state -> unknown

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	DOWN	OK
EOF
# ASSERT: 0	0	1000	100.0000
