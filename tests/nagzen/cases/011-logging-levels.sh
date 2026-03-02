#!/bin/bash
# Test: Verify logging levels (notice, info, debug)
#
# Verifies:
# - notice() always shows (VERBOSE >= 0)
# - warning() always shows (VERBOSE >= 0)
# - info() shows only at VERBOSE >= 1
# - debug() shows only at VERBOSE >= 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAGZEN_SCRIPT="${SCRIPT_DIR}/../../../scripts/nagzen"

# Colors
RED='\033[1;91m'
GREEN='\033[1;92m'
NC='\033[0m'

FAILED=0

# Test helper: check if pattern exists in output
check_output() {
    local desc="$1"
    local pattern="$2"
    local output="$3"
    local should_exist="$4"  # 1=should exist, 0=should not exist

    if [[ $should_exist -eq 1 ]]; then
        if echo "$output" | grep -q "$pattern"; then
            echo -e "${GREEN}PASS${NC} $desc"
        else
            echo -e "${RED}FAIL${NC} $desc (expected '$pattern' not found)"
            ((FAILED++))
        fi
    else
        if echo "$output" | grep -q "$pattern"; then
            echo -e "${RED}FAIL${NC} $desc (unexpected '$pattern' found)"
            ((FAILED++))
        else
            echo -e "${GREEN}PASS${NC} $desc"
        fi
    fi
}

# Run test with specific VERBOSE level
run_logging_test() {
    local verbose_level="$1"
    (
        set +u
        export VERBOSE=$verbose_level
        export XDEBUG=0
        source "$NAGZEN_SCRIPT"
        notice "test-notice-msg"
        warning "test-warning-msg"
        info "test-info-msg"
        debug "test-debug-msg"
    ) 2>&1
}

echo "Testing logging levels..."
echo ""

# Test VERBOSE=0 (only notice/warning should show)
output=$(run_logging_test 0)
check_output "VERBOSE=0: notice shows"    "NOTICE.*test-notice-msg"   "$output" 1
check_output "VERBOSE=0: warning shows"   "WARNING.*test-warning-msg" "$output" 1
check_output "VERBOSE=0: info hidden"     "INFO.*test-info-msg"       "$output" 0
check_output "VERBOSE=0: debug hidden"    "DEBUG.*test-debug-msg"     "$output" 0

echo ""

# Test VERBOSE=1 (notice/warning/info should show)
output=$(run_logging_test 1)
check_output "VERBOSE=1: notice shows"    "NOTICE.*test-notice-msg"   "$output" 1
check_output "VERBOSE=1: warning shows"   "WARNING.*test-warning-msg" "$output" 1
check_output "VERBOSE=1: info shows"      "INFO.*test-info-msg"       "$output" 1
check_output "VERBOSE=1: debug hidden"    "DEBUG.*test-debug-msg"     "$output" 0

echo ""

# Test VERBOSE=2 (all should show)
output=$(run_logging_test 2)
check_output "VERBOSE=2: notice shows"    "NOTICE.*test-notice-msg"   "$output" 1
check_output "VERBOSE=2: warning shows"   "WARNING.*test-warning-msg" "$output" 1
check_output "VERBOSE=2: info shows"      "INFO.*test-info-msg"       "$output" 1
check_output "VERBOSE=2: debug shows"     "DEBUG.*test-debug-msg"     "$output" 1

echo ""

# Test debug with custom level (-3)
run_debug_level_test() {
    local verbose_level="$1"
    (
        set +u
        export VERBOSE=$verbose_level
        export XDEBUG=0
        source "$NAGZEN_SCRIPT"
        debug -3 "test-debug-level3-msg"
    ) 2>&1
}

output=$(run_debug_level_test 2)
check_output "VERBOSE=2: debug -3 hidden" "DEBUG.*test-debug-level3-msg" "$output" 0

output=$(run_debug_level_test 3)
check_output "VERBOSE=3: debug -3 shows"  "DEBUG.*test-debug-level3-msg" "$output" 1

echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}All logging tests passed${NC}"
    exit 0
else
    echo -e "${RED}$FAILED logging test(s) failed${NC}"
    exit 1
fi
