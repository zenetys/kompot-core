#!/bin/bash
# Test: Initial states set before period
# Period: 500-1000
#
# States are set at t=0, before the period starts
# The script should use these as initial states at period start
#
# sql: OK at t=0, CRITICAL at t=700
# www: OK at t=0
#
# At period start (500): sql=OK, www=OK → OK
# At t=700: sql=CRITICAL → group CRITICAL
#
# Available: 200s (500-700)
# Unavailable: 300s (700-1000)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=500 -v BEFORE=1000 -v OP=AND
0	sql	OK
0	www	OK
700	sql	CRITICAL
EOF
# ASSERT: 200	300	0	40.0000
