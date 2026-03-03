#!/bin/bash
# Test: Host UNREACHABLE + Service CRITICAL = Unknown
# Period: 0-1000
# Host UNREACHABLE takes precedence, we cannot determine service state

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UNREACHABLE	CRITICAL
EOF
# ASSERT: 0	0	1000	100.0000
