#!/bin/bash
# Test: Host UP + Service OK = Available
# Period: 0-1000
# 3-column mode: timestamp, host_state, service_state

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UP	OK
EOF
# ASSERT: 1000	0	0	100.0000
