#!/bin/bash
# Test: AND mode - three members
# Period: 0-1000
#
# web:  ████████████████  (OK entire period)
# sql:  ████████░░░░░░░░  (OK 0-500, CRITICAL 500-1000)
# cache:░░░░████████████  (CRITICAL 0-200, OK 200-1000)
#       ─────────────────
# grp:  ░░░░████░░░░░░░░  (OK 200-500 only) → 30% dispo
#
# Available: 300s (200-500)
# Unavailable: 700s

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=AND
0	web	OK
0	sql	OK
0	cache	CRITICAL
200	cache	OK
500	sql	CRITICAL
EOF
# ASSERT: 300	700	0	30.0000
