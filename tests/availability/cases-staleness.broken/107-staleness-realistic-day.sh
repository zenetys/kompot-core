#!/bin/bash
# Test: Realistic day scenario with staleness (86400s/day, stale after 1 day)
# Period: 0-172800 (2 days), STALE_AFTER=86400 (1 day)
# OK at start of day 1
# At 86400 (start of day 2), data becomes stale
#
# Day 1 (0-86400): OK (fresh) = 86400s available
# Day 2 (86400-172800): UNKNOWN (stale) = 86400s unknown
#
# Availability: 86400 / 86400 = 100%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=172800 -v STALE_AFTER=86400
0	OK
EOF
# ASSERT: 86400	0	86400	100.0000
