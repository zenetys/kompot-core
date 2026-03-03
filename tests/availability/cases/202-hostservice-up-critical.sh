#!/bin/bash
# Test: Host UP + Service CRITICAL = Unavailable
# Period: 0-1000

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UP	CRITICAL
EOF
# ASSERT: 0	1000	0	0.0000
