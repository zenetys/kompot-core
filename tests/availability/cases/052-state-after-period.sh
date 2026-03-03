#!/bin/bash
# Test: State changes after period end (should be ignored)
# Period: 1000-2000
# Initial: OK at 500
# Transitions after period: CRITICAL at 2500, WARNING at 3000
# Should only consider OK state during period

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000
500	OK
2500	CRITICAL
3000	WARNING
EOF
# ASSERT: 1000	0	0	100.0000
