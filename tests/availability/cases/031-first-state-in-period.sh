#!/bin/bash
# Test: First state occurs during period (no initial state)
# Period: 0-1000, first state at 300
# 0-300: unknown (no data)
# 300-1000: OK (700s)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
300	OK
EOF
# ASSERT: 700	0	300	100.0000
