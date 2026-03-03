#!/bin/bash
# Test: UNKNOWN state in middle of period
# Period: 0-1000
# 0-300: OK (300s)
# 300-600: UNKNOWN (300s) - not counted
# 600-1000: CRITICAL (400s)
# Availability: 300 / (300 + 400) = 42.857%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	OK
300	UNKNOWN
600	CRITICAL
EOF
# ASSERT: 300	400	300	42.8571
