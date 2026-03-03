#!/bin/bash
# Test: Host UP state for entire period = 100% availability
# UP is the host equivalent of OK

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	UP
EOF
# ASSERT: 1000	0	0	100.0000
