#!/bin/bash
# Test: Multiple transitions with staleness
# Period: 0-1000, STALE_AFTER=200
# 0: OK, becomes stale at 200
# 300: CRITICAL, becomes stale at 500
# 600: OK, becomes stale at 800
#
# Timeline:
# 0-200: OK (fresh) = 200s available
# 200-300: UNKNOWN (stale) = 100s unknown
# 300-500: CRITICAL (fresh) = 200s unavailable
# 500-600: UNKNOWN (stale) = 100s unknown
# 600-800: OK (fresh) = 200s available
# 800-1000: UNKNOWN (stale) = 200s unknown
#
# Total: 400s available, 200s unavailable, 400s unknown
# Availability: 400 / 600 = 66.6667%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v STALE_AFTER=200
0	OK
300	CRITICAL
600	OK
EOF
# ASSERT: 400	200	400	66.6667
