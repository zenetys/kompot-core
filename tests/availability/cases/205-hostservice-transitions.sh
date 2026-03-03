#!/bin/bash
# Test: Host+Service with state transitions
# Period: 0-1000
#
# Timeline:
# 0-300:    UP + OK       = AVAILABLE (300s)
# 300-500:  DOWN + OK     = UNKNOWN (200s) <- host DOWN = cannot determine
# 500-800:  UP + CRITICAL = UNAVAILABLE (300s)
# 800-1000: UP + OK       = AVAILABLE (200s)
#
# Total: 500s available, 300s unavailable, 200s unknown
# Availability: 500/(500+300) = 62.5%

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	UP	OK
300	DOWN	OK
500	UP	CRITICAL
800	UP	OK
EOF
# ASSERT: 500	300	200	62.5000
