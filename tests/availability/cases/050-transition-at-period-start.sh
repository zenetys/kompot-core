#!/bin/bash
# Test: State change exactly at period start
# Period: 1000-2000
# Initial: CRITICAL at 500
# Transition: OK at 1000 (exactly at period start)
# Entire period should be OK

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	CRITICAL
1000	OK
EOF
# ASSERT: 1000	0	0	100.0000
