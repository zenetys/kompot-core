#!/bin/bash
# Test: Multiple state changes before period - last one should be used
# States: OK at 100, CRITICAL at 200, WARNING at 300
# Period: 1000-2000
# Should use WARNING (last state before period)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
100	OK
200	CRITICAL
300	WARNING
EOF
# ASSERT: 1000	0	0	100.0000
