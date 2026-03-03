#!/bin/bash
# Test: Simple transition from OK to CRITICAL
# Period: 0-1000, transition at 500

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	OK
500	CRITICAL
EOF
# ASSERT: 500	500	0	50.0000
