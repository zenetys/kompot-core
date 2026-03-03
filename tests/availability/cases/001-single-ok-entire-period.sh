#!/bin/bash
# Test: Single OK state for entire period = 100% availability
# Period: 1000 seconds, entirely in OK state

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	OK
EOF
# ASSERT: 1000	0	0	100.0000
