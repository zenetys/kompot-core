#!/bin/bash
# Test: Initial state becomes stale during period
# Period: 1000-2000, STALE_AFTER=1200
# OK at 0, becomes stale at 1200 (200s into period)
# 0-1000: before period
# 1000-1200: OK (fresh) - 200s
# 1200-2000: UNKNOWN (stale) - 800s
# Availability: 200 / 200 = 100%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=1000 -v BEFORE=2000 -v STALE_AFTER=1200
0	OK
EOF
# ASSERT: 200	0	800	100.0000
