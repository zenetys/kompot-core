#!/bin/bash
# Test: Initial state already stale at period start
# Period: 1000-2000, STALE_AFTER=500
# OK at 0 (1000s before period), stale since 500
# At period start (1000), already stale for 500s
# Entire period should be UNKNOWN

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000 -v STALE_AFTER=500
0	OK
EOF
# ASSERT: 0	0	1000	100.0000
