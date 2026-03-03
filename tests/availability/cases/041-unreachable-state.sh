#!/bin/bash
# Test: UNREACHABLE state (host state, treated like UNKNOWN)
# Period: 0-1000
# 0-500: UP (500s)
# 500-1000: UNREACHABLE (500s) - not counted
# Availability: 500 / 500 = 100%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UP
500	UNREACHABLE
EOF
# ASSERT: 500	0	500	100.0000
