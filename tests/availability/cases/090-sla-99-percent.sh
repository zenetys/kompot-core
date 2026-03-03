#!/bin/bash
# Test: Realistic SLA scenario - 99% availability
# Period: 30 days = 2592000 seconds
# Downtime: 1% = 25920 seconds
# Available: 2566080 seconds

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=2592000
0	OK
2566080	CRITICAL
EOF
# ASSERT: 2566080	25920	0	99.0000
