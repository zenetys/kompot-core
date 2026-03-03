#!/bin/bash
# ==============================================
# Availability Calculation Test Runner
# Tests the availability-calc algorithm
# ==============================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASES_DIR="${SCRIPT_DIR}/cases"
CALC_SCRIPT="${CALC_SCRIPT:-${SCRIPT_DIR}/../../scripts/availability-calc}"

# Configuration
VERBOSE=${VERBOSE:-0}
NAME_WIDTH=${NAME_WIDTH:-55}
UPDATE_EXPECTED=${UPDATE_EXPECTED:-0}

# Colors (disabled if no tty)
if [[ -t 1 ]]; then
    RED='\033[1;91m'
    GREEN='\033[1;92m'
    YELLOW='\033[1;93m'
    CYAN='\033[1;96m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    CYAN=''
    BOLD=''
    NC=''
fi

# Counters
TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

# Temp directory for test artifacts
WORK_DIR=$(mktemp -d)
trap "rm -rf $WORK_DIR" EXIT

# Run a test script and capture output
run_test() {
    local test_script="$1"
    local output_file="$2"

    (
        export WORK_DIR
        export CALC_SCRIPT
        bash "$test_script"
    ) > "$output_file" 2>&1

    return $?
}

# Normalize output for comparison
normalize_output() {
    local file="$1"
    sed 's/[[:space:]]*$//' "$file" | cat -s
}

# Extract inline ASSERT from test file
# Returns expected output via stdout, empty if no ASSERT found
extract_assert() {
    local test_file="$1"
    grep '^# ASSERT:' "$test_file" | sed 's/^# ASSERT:[[:space:]]*//'
}

# Run a single test case
run_test_case() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .sh)
    local expected_file="${test_file%.sh}.expected"

    ((TOTAL++))

    # Check if test file exists
    if [[ ! -f "$test_file" ]]; then
        printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s\n" "$test_name" "Test file not found"
        ((FAILED++))
        return 1
    fi

    # Check for skip marker
    if head -1 "$test_file" | grep -q '^# SKIP'; then
        local skip_reason=$(head -1 "$test_file" | sed 's/^# SKIP[: ]*//')
        printf "${YELLOW}SKIP${NC} %-${NAME_WIDTH}s %s\n" "$test_name" "${skip_reason:-skipped}"
        ((SKIPPED++))
        return 0
    fi

    # Check for inline ASSERT or .expected file
    local inline_assert
    inline_assert=$(extract_assert "$test_file")

    if [[ -z "$inline_assert" ]] && [[ ! -f "$expected_file" ]]; then
        if [[ "$UPDATE_EXPECTED" == "1" ]]; then
            run_test "$test_file" "$expected_file"
            printf "${YELLOW}NEW ${NC} %-${NAME_WIDTH}s %s\n" "$test_name" "Created expected file"
            ((SKIPPED++))
            return 0
        else
            printf "${YELLOW}SKIP${NC} %-${NAME_WIDTH}s %s\n" "$test_name" "No ASSERT or .expected file"
            ((SKIPPED++))
            return 0
        fi
    fi

    # Check for expected error marker
    local expect_error=0
    if head -5 "$test_file" | grep -q '^# EXPECT_ERROR'; then
        expect_error=1
    fi

    # Start timing
    local start_time=$(date +%s%3N)

    # Run test
    local actual_file="$WORK_DIR/${test_name}.actual"
    run_test "$test_file" "$actual_file"
    local exit_code=$?

    # Calculate elapsed time
    local end_time=$(date +%s%3N)
    local elapsed_ms=$((end_time - start_time))
    local elapsed_str
    if [[ $elapsed_ms -ge 1000 ]]; then
        elapsed_str=$(awk "BEGIN {printf \"%.1fs\", $elapsed_ms/1000}")
    else
        elapsed_str="${elapsed_ms}ms"
    fi

    # Validate exit code
    if [[ "$expect_error" == "1" && "$exit_code" == "0" ]]; then
        printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Expected error but got success" "$elapsed_str"
        ((FAILED++))
        return 1
    elif [[ "$expect_error" == "0" && "$exit_code" != "0" ]]; then
        printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Unexpected error (exit $exit_code)" "$elapsed_str"
        if [[ "$VERBOSE" == "1" ]]; then
            echo -e "  ${RED}Output:${NC}"
            head -20 "$actual_file" | sed 's/^/  /'
        fi
        ((FAILED++))
        return 1
    fi

    # Compare output with expected (inline ASSERT takes precedence over .expected file)
    local diff_file="$WORK_DIR/${test_name}.diff"
    local expected_content
    if [[ -n "$inline_assert" ]]; then
        expected_content="$inline_assert"
    else
        expected_content=$(normalize_output "$expected_file")
    fi

    if ! diff -u <(echo "$expected_content") <(normalize_output "$actual_file") > "$diff_file" 2>&1; then
        if [[ "$UPDATE_EXPECTED" == "1" ]] && [[ -z "$inline_assert" ]]; then
            cp "$actual_file" "$expected_file"
            printf "${YELLOW}UPD ${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Updated expected file" "$elapsed_str"
            ((PASSED++))
            return 0
        fi

        printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Output mismatch" "$elapsed_str"

        local diff_lines=$(wc -l < "$diff_file")
        if [[ "$VERBOSE" == "1" ]] || [[ $diff_lines -le 30 ]]; then
            echo -e "  ${CYAN}Diff:${NC}"
            while IFS= read -r line; do
                case "${line:0:1}" in
                    '-') echo -e "  ${RED}${line}${NC}" ;;
                    '+') echo -e "  ${GREEN}${line}${NC}" ;;
                    '@') echo -e "  ${CYAN}${line}${NC}" ;;
                    *)   echo "  $line" ;;
                esac
            done < "$diff_file" | head -30
            [[ $diff_lines -gt 30 ]] && echo "  ... ($diff_lines lines total)"
        else
            echo "  Run with VERBOSE=1 to see diff ($diff_lines lines)"
        fi

        ((FAILED++))
        return 1
    fi

    printf "${GREEN}PASS${NC} %-${NAME_WIDTH}s ${CYAN}(%s)${NC}\n" "$test_name" "$elapsed_str"
    ((PASSED++))
    return 0
}

# Print usage
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [TEST_NAME...]

Availability calculation test runner.

Options:
  -v, --verbose         Show detailed diff output for failures
  -u, --update          Update/create .expected files from actual output
  -h, --help            Show this help

Environment variables:
  VERBOSE=1             Same as --verbose
  UPDATE_EXPECTED=1     Same as --update
  NAME_WIDTH=55         Test name column width

Test file markers:
  # SKIP [reason]       Skip this test
  # EXPECT_ERROR        Test should fail (exit non-zero)
  # ASSERT: <expected>  Inline expected output (replaces .expected file)

Examples:
  $0                              # Run all tests
  $0 001-single-ok                # Run specific test
  $0 -v                           # Verbose mode
  $0 -u                           # Update expected files

EOF
    exit 0
}

# Main entry point
main() {
    echo -e "${BOLD}Availability Calculation Tests${NC}"
    echo ""

    # Check calc script exists
    if [[ ! -f "$CALC_SCRIPT" ]]; then
        echo -e "${RED}FAIL${NC} availability-calc script not found: $CALC_SCRIPT"
        exit 1
    fi

    # Find test files
    local test_files=()
    if [[ $# -gt 0 ]]; then
        for arg in "$@"; do
            if [[ -f "$CASES_DIR/$arg.sh" ]]; then
                test_files+=("$CASES_DIR/$arg.sh")
            elif [[ -f "$arg" ]]; then
                test_files+=("$arg")
            elif [[ -f "$arg.sh" ]]; then
                test_files+=("$arg.sh")
            else
                echo -e "${RED}FAIL${NC} Test not found: $arg"
            fi
        done
    else
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find "$CASES_DIR" -name '*.sh' -print0 2>/dev/null | sort -z)
    fi

    if [[ ${#test_files[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No test files found in $CASES_DIR${NC}"
        echo "Create test files as: cases/XXX-test-name.sh"
        echo "Run with UPDATE_EXPECTED=1 to generate .expected files"
        exit 0
    fi

    # Run tests
    for test_file in "${test_files[@]}"; do
        run_test_case "$test_file" || true
    done

    # Summary
    echo ""
    local summary="${GREEN}$PASSED passed${NC}"
    [[ $FAILED -gt 0 ]] && summary="$summary, ${RED}$FAILED failed${NC}"
    [[ $SKIPPED -gt 0 ]] && summary="$summary, ${YELLOW}$SKIPPED skipped${NC}"
    echo -e "$summary ${CYAN}(total: $TOTAL)${NC}"

    [[ $FAILED -eq 0 ]] && exit 0 || exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -u|--update)
            UPDATE_EXPECTED=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            ;;
        *)
            break
            ;;
    esac
done

main "$@"
