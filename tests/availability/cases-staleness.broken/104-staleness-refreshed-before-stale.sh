#!/bin/bash
# Test: State refreshed before becoming stale
# Period: 0-1000, STALE_AFTER=300
# OK at 0, OK again at 200 (refreshes freshness), OK again at 400
# 0-200: OK fresh
# 200-400: OK fresh (refreshed at 200)
# 400-700: OK fresh (refreshed at 400)
# 700-1000: UNKNOWN (stale since 400+300=700)
# Availability: 700 / 700 = 100%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000 -v STALE_AFTER=300
0	OK
200	OK
400	OK
EOF
# ASSERT: 700	0	300	100.0000
