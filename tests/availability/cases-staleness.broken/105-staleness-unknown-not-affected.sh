#!/bin/bash
# Test: UNKNOWN state is not affected by staleness
# Period: 0-1000, STALE_AFTER=300
# UNKNOWN at 0 - staleness doesn't apply to UNKNOWN state
# Should be 1000s unknown (not split into fresh/stale)
# Availability: 100% (no counted time)

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v STALE_AFTER=300
0	UNKNOWN
EOF
# ASSERT: 0	0	1000	100.0000
