#!/bin/bash
# Test: Initial state before period with transition during period
# State OK at t=500, changes to CRITICAL at t=1500
# Period: 1000-2000
# 1000-1500: OK (500s)
# 1500-2000: CRITICAL (500s)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	OK
1500	CRITICAL
EOF
# ASSERT: 500	500	0	50.0000
