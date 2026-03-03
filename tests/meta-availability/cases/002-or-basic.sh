#!/bin/bash
# Test: OR mode - basic redundancy
# Period: 0-1000
#
# sql: ████████░░░░░░░░  (OK 0-500, CRITICAL 500-1000)
# www: ░░░░░████████████  (CRITICAL 0-300, OK 300-1000)
#      ─────────────────
# grp: ████████████████  (always at least one OK) → 100% dispo
#
# Available: 1000s (entire period)
# Unavailable: 0s

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=OR
0	sql	OK
0	www	CRITICAL
300	www	OK
500	sql	CRITICAL
EOF
# ASSERT: 1000	0	0	100.0000
