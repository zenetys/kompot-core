#!/bin/bash
# Test: Precise percentage calculation
# Period: 0-10000
# 0-9990: OK (9990s)
# 9990-10000: CRITICAL (10s)
# Availability: 9990 / 10000 = 99.9%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=10000
0	OK
9990	CRITICAL
EOF
# ASSERT: 9990	10	0	99.9000
