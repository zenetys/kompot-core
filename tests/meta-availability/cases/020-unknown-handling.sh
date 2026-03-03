#!/bin/bash
# Test: AND mode with UNKNOWN state
# Period: 0-1000
#
# sql: ████████████████  (OK entire period)
# www: ░░░░░░░░████████  (UNKNOWN 0-400, OK 400-1000)
#      ─────────────────
# grp: ░░░░░░░░████████  (OK only when both are OK/known)
#
# Available: 600s (400-1000)
# Unknown: 400s (0-400, www is unknown)
# Unavailable: 0s

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=AND
0	sql	OK
0	www	UNKNOWN
400	www	OK
EOF
# ASSERT: 600	0	400	100.0000
