#!/bin/bash
# Test: OR mode - three members (N+2 redundancy)
# Period: 0-1000
#
# web1: ████░░░░░░░░░░░░  (OK 0-200, CRITICAL 200-1000)
# web2: ░░░░████░░░░░░░░  (CRITICAL 0-200, OK 200-500, CRITICAL 500-1000)
# web3: ░░░░░░░░████████  (CRITICAL 0-500, OK 500-1000)
#       ─────────────────
# grp:  ████████████████  (always at least one OK) → 100% dispo
#
# Each server is only partially available, but together they cover 100%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v OP=OR
0	web1	OK
0	web2	CRITICAL
0	web3	CRITICAL
200	web1	CRITICAL
200	web2	OK
500	web2	CRITICAL
500	web3	OK
EOF
# ASSERT: 1000	0	0	100.0000
