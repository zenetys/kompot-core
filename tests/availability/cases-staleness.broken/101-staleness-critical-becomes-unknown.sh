#!/bin/bash
# Test: CRITICAL state becomes stale
# Period: 0-1000, STALE_AFTER=300
# CRITICAL at 0
# First 300s: CRITICAL (fresh), next 700s: UNKNOWN (stale)
# Availability: 0 / 300 = 0%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v STALE_AFTER=300
0	CRITICAL
EOF
# ASSERT: 0	300	700	0.0000
