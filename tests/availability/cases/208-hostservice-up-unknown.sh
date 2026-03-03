#!/bin/bash
# Test: Host UP + Service UNKNOWN = Unknown
# Period: 0-1000
# Service state is unknown, so effective state is unknown

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UP	UNKNOWN
EOF
# ASSERT: 0	0	1000	100.0000
