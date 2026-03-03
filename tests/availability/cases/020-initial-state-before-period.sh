#!/bin/bash
# Test: Initial state set before period, no changes during period
# State set at t=500, period 1000-2000
# Entire period should be in OK state

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	OK
EOF
# ASSERT: 1000	0	0	100.0000
