#!/bin/bash
# Test: State change exactly at period end (should be ignored)
# Period: 1000-2000
# Initial: OK at 500
# Transition: CRITICAL at 2000 (exactly at period end - should not count)
# Entire period should be OK

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	OK
2000	CRITICAL
EOF
# ASSERT: 1000	0	0	100.0000
