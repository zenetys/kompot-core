#!/bin/bash
# Test: Simple transition from CRITICAL to OK
# Period: 0-1000, transition at 200

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	CRITICAL
200	OK
EOF
# ASSERT: 800	200	0	80.0000
