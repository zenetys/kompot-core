#!/bin/bash
# Test: Host UP + Service WARNING = Available
# Period: 0-1000
# WARNING is considered available (service is working, just degraded)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UP	WARNING
EOF
# ASSERT: 1000	0	0	100.0000
