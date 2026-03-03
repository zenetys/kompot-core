#!/bin/bash
# Test: Single WARNING state for entire period = 100% availability
# WARNING counts as "available"

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	WARNING
EOF
# ASSERT: 1000	0	0	100.0000
