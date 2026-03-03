#!/bin/bash
# Test: Multiple transitions all in UNKNOWN state
# Period: 0-1000
# Should still be 100% availability (no counted time)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UNKNOWN
300	UNREACHABLE
600	UNKNOWN
EOF
# ASSERT: 0	0	1000	100.0000
