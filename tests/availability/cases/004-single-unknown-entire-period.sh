#!/bin/bash
# Test: Single UNKNOWN state for entire period
# UNKNOWN is ignored in percentage calculation, so 100% by convention

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	UNKNOWN
EOF
# ASSERT: 0	0	1000	100.0000
