#!/bin/bash
# Test: OR mode with UNKNOWN state
# Period: 0-1000
#
# sql: ████████████████  (OK entire period)
# www: ░░░░░░░░████████  (UNKNOWN 0-400, OK 400-1000)
#      ─────────────────
# grp: ████████████████  (sql is OK, so group is OK)
#
# OR mode: if one is OK, group is OK regardless of UNKNOWN

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=OR
0	sql	OK
0	www	UNKNOWN
400	www	OK
EOF
# ASSERT: 1000	0	0	100.0000
