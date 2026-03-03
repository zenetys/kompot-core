#!/bin/bash
# Test: Host DOWN + Service CRITICAL = UNKNOWN
# Period: 0-1000
# Even though service is CRITICAL, host is DOWN so we cannot determine state

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	DOWN	CRITICAL
EOF
# ASSERT: 0	0	1000	100.0000
