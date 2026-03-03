#!/bin/bash
# Test: Single CRITICAL state for entire period = 0% availability
# Period: 1000 seconds, entirely in CRITICAL state

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	CRITICAL
EOF
# ASSERT: 0	1000	0	0.0000
