#!/bin/bash
# Test: Host UNREACHABLE state for entire period = unknown
# Period: 1000 seconds, entirely in UNREACHABLE state

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UNREACHABLE
EOF
# ASSERT: 0	0	1000	100.0000
