#!/bin/bash
# Test: Host DOWN state for entire period = 0% availability
# DOWN is the host equivalent of CRITICAL

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	DOWN
EOF
# ASSERT: 0	1000	0	0.0000
