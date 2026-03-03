#!/bin/bash
# Test: No state data at all
# Period: 1000-2000
# By convention, no data = 100% availability (but 100% unknown)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
EOF
# ASSERT: 0	0	1000	100.0000
