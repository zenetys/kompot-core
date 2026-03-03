#!/bin/bash
# Test: Host DOWN + Service UNKNOWN = Unknown (ignored)
# Period: 0-1000

cat << 'EOF' | "$CALC_SCRIPT" -v SINCE=0 -v BEFORE=1000
0	DOWN	UNKNOWN
EOF
# ASSERT: 0	0	1000	100.0000
