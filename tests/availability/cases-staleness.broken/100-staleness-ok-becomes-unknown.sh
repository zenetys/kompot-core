#!/bin/bash
# Test: OK state becomes stale
# Period: 0-1000, STALE_AFTER=500
# OK at 0, stays OK until period end
# First 500s: OK (fresh), next 500s: UNKNOWN (stale)
# Availability: 500 / 500 = 100% (stale period not counted)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v STALE_AFTER=500
0	OK
EOF
# ASSERT: 500	0	500	100.0000
