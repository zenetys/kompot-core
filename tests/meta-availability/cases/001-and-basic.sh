#!/bin/bash
# Test: AND mode - basic overlap
# Period: 0-1000
#
# sql: ████████░░░░░░░░  (OK 0-500, CRITICAL 500-1000)
# www: ░░░░░████████████  (CRITICAL 0-300, OK 300-1000)
#      ─────────────────
# grp: ░░░░░███░░░░░░░░░  (OK 300-500 only) → 20% dispo
#
# Available: 200s (300-500)
# Unavailable: 800s (0-300 + 500-1000)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=AND
0	sql	OK
0	www	CRITICAL
300	www	OK
500	sql	CRITICAL
EOF
# ASSERT: 200	800	0	20.0000
