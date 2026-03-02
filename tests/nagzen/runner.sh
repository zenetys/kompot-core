#!/bin/bash
# ==============================================
# Nagzen Configuration Generator Test Runner
# Executes .cfg test cases and validates output
# ==============================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASES_DIR="${SCRIPT_DIR}/cases"
NAGZEN_SCRIPT="${SCRIPT_DIR}/../../scripts/nagzen"
TEMPLATES_DIR="${SCRIPT_DIR}/../../configs/nagzen/templates"

# Configuration
VERBOSE=${VERBOSE:-0}
NAME_WIDTH=${NAME_WIDTH:-50}
UPDATE_EXPECTED=${UPDATE_EXPECTED:-0}
DIFF_TOOL=${DIFF_TOOL:-diff}
VALIDATE_NAGIOS=${VALIDATE_NAGIOS:-0}
NAGIOS_BIN=${NAGIOS_BIN:-/usr/sbin/nagios}
NAGIOS_CFG_TEMPLATE="${SCRIPT_DIR}/nagios-test.cfg"
NAGIOS_HARNESS="${SCRIPT_DIR}/nagios-harness.cfg"

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

# Captured stderr from last nagzen run
NAGZEN_STDERR=""

# Run nagzen on a source file and capture output
# Sets NAGZEN_STDERR with any error messages
run_nagzen() {
    local source_file="$1"
    local output_file="$2"
    local with_templates="${3:-0}"
    local stderr_file="$WORK_DIR/nagzen_stderr.tmp"

    NAGZEN_STDERR=""

    (
        # Disable strict unbound variable check (nagzen doesn't use it)
        set +u

        # Save trace state and disable it during test execution
        # This prevents 'set -x' output from polluting test diffs
        local _trace_was_on=0
        [[ $- == *x* ]] && _trace_was_on=1
        set +x

        # Set required environment variables for nagzen
        # Force XDEBUG=0 to prevent trace output in test results
        export XDEBUG=0
        export DEBUG=${DEBUG:-0}
        export VERBOSE=${VERBOSE:-0}

        # Source nagzen functions
        source "$NAGZEN_SCRIPT"

        # Optionally load templates (output goes to /dev/null, we only want state)
        # This simulates what update-nagios does: source templates in numeric order
        # Note: nagzen sets "set -f" (noglob), so we need to re-enable glob temporarily
        if [[ "$with_templates" == "1" ]]; then
            local tpl
            local tpl_files
            set +f  # Re-enable glob expansion
            tpl_files=( "$TEMPLATES_DIR"/*.cfg )
            set -f  # Restore noglob
            for tpl in "${tpl_files[@]}"; do
                [[ -f "$tpl" ]] || continue
                # Source template, redirect output (we only want the state: HOSTS[], SERVICES[], etc.)
                source "$tpl" > /dev/null
                # Close any pending host from this template file
                host-end > /dev/null 2>&1 || true
            done
        fi

        # Source the test file (this output we capture)
        source "$source_file"

        # Trigger host-end for any pending host
        host-end 2>/dev/null || true

        # Restore trace state
        (( _trace_was_on )) && set -x || true
    ) > "$output_file" 2>"$stderr_file"

    local exit_code=$?

    # Capture stderr for error reporting
    if [[ -s "$stderr_file" ]]; then
        NAGZEN_STDERR=$(cat "$stderr_file")
    fi

    return $exit_code
}

# Validate generated config with nagios -v
validate_nagios() {
    local objects_file="$1"
    local nagios_work_dir="$2"

    # Check if nagios binary exists
    if [[ ! -x "$NAGIOS_BIN" ]]; then
        echo "SKIP: nagios not found at $NAGIOS_BIN"
        return 2
    fi

    # Check if config template exists
    if [[ ! -f "$NAGIOS_CFG_TEMPLATE" ]]; then
        echo "SKIP: nagios config template not found"
        return 2
    fi

    # Create nagios.cfg with proper paths
    local user=$(id -un)
    local group=$(id -gn)

    sed -e "s|WORK_DIR_PLACEHOLDER|$nagios_work_dir|g" \
        -e "s|USER_PLACEHOLDER|$user|g" \
        -e "s|GROUP_PLACEHOLDER|$group|g" \
        -e "s|HARNESS_FILE_PLACEHOLDER|$NAGIOS_HARNESS|g" \
        -e "s|OBJECTS_FILE_PLACEHOLDER|$objects_file|g" \
        "$NAGIOS_CFG_TEMPLATE" > "$nagios_work_dir/nagios.cfg"

    # Run nagios -v
    local output
    output=$("$NAGIOS_BIN" -v "$nagios_work_dir/nagios.cfg" 2>&1)
    local exit_code=$?

    if [[ $exit_code -ne 0 ]]; then
        echo "$output" | grep -E "^Error:" | head -5
        return 1
    fi

    return 0
}

# Parse nagios precache file and extract host/service attributes
# Output format: type:hostname:service:attr=value or type:hostname:attr=value
parse_precache() {
    local precache_file="$1"
    awk '
    BEGIN { in_block = 0; block_type = "" }
    /^define (host|service) \{/ {
        in_block = 1
        block_type = $2
        host_name = ""
        service_desc = ""
        delete attrs
        next
    }
    /^\t\}/ {
        if (in_block && block_type == "service" && host_name && service_desc) {
            for (attr in attrs) {
                print "service:" host_name ":" service_desc ":" attr "=" attrs[attr]
            }
        }
        if (in_block && block_type == "host" && host_name) {
            for (attr in attrs) {
                print "host:" host_name ":" attr "=" attrs[attr]
            }
        }
        in_block = 0
        next
    }
    in_block && /^\t[a-zA-Z_]+\t/ {
        gsub(/^\t/, "")
        gsub(/\t+/, "\t")
        n = split($0, parts, "\t")
        attr_name = parts[1]
        attr_value = parts[2]
        gsub(/ $/, "", attr_value)
        if (attr_name == "host_name") host_name = attr_value
        else if (attr_name == "service_description") service_desc = attr_value
        else attrs[attr_name] = attr_value
    }
    ' "$precache_file"
}

# Validate assertions from test file against nagios precache
# Returns 0 if all assertions pass, 1 if any fail
validate_assertions() {
    local test_file="$1"
    local objects_file="$2"
    local nagios_work_dir="$3"
    local failed=0

    # Extract assertions from test file
    local assertions
    assertions=$(grep '^# ASSERT ' "$test_file" | sed 's/^# ASSERT //')

    if [[ -z "$assertions" ]]; then
        return 0  # No assertions to check
    fi

    # Check if nagios binary exists
    if [[ ! -x "$NAGIOS_BIN" ]]; then
        echo "SKIP: nagios not found"
        return 2
    fi

    # Generate precache
    local user=$(id -un)
    local group=$(id -gn)

    sed -e "s|WORK_DIR_PLACEHOLDER|$nagios_work_dir|g" \
        -e "s|USER_PLACEHOLDER|$user|g" \
        -e "s|GROUP_PLACEHOLDER|$group|g" \
        -e "s|HARNESS_FILE_PLACEHOLDER|$NAGIOS_HARNESS|g" \
        -e "s|OBJECTS_FILE_PLACEHOLDER|$objects_file|g" \
        "$NAGIOS_CFG_TEMPLATE" > "$nagios_work_dir/nagios.cfg"

    if ! "$NAGIOS_BIN" -vp "$nagios_work_dir/nagios.cfg" > "$nagios_work_dir/nagios_output.txt" 2>&1; then
        echo "Nagios precache generation failed"
        return 1
    fi

    local precache_file="$nagios_work_dir/objects.precache"
    if [[ ! -f "$precache_file" ]]; then
        echo "Precache file not found"
        return 1
    fi

    # Parse precache into searchable format
    local parsed_file="$nagios_work_dir/parsed.txt"
    parse_precache "$precache_file" > "$parsed_file"

    # Check each assertion
    local assertion
    while IFS= read -r assertion; do
        [[ -z "$assertion" ]] && continue

        # Check for negative assertion (starts with !)
        if [[ "${assertion:0:1}" == "!" ]]; then
            local neg_pattern="${assertion:1}"
            if grep -qF "$neg_pattern" "$parsed_file"; then
                echo "FAIL: $assertion (should NOT exist)"
                local actual=$(grep -F "$neg_pattern" "$parsed_file" | head -1)
                echo "  found: $actual"
                failed=1
            fi
        else
            # Positive assertion
            if ! grep -qF "$assertion" "$parsed_file"; then
                echo "FAIL: $assertion"
                # Show actual value if attribute exists
                local pattern=$(echo "$assertion" | sed 's/=[^=]*$/=/')
                local actual=$(grep -F "$pattern" "$parsed_file" | head -1)
                if [[ -n "$actual" ]]; then
                    echo "  got: $actual"
                else
                    echo "  not found in precache"
                fi
                failed=1
            fi
        fi
    done <<< "$assertions"

    return $failed
}

# Normalize output for comparison (remove empty lines, trim whitespace)
normalize_output() {
    local file="$1"
    # Remove trailing whitespace, normalize multiple blank lines
    sed 's/[[:space:]]*$//' "$file" | cat -s
}

# Run a single test case
run_test_case() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .cfg)
    local test_dir=$(dirname "$test_file")
    local expected_file="${test_file%.cfg}.expected"
    local with_templates=0

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

    # Check for template loading marker
    if head -5 "$test_file" | grep -q '^# WITH_TEMPLATES'; then
        with_templates=1
    fi

    # Check for skip nagios validation marker
    local skip_nagios=0
    if head -5 "$test_file" | grep -q '^# SKIP_NAGIOS'; then
        skip_nagios=1
    fi

    # Check if expected file exists
    if [[ ! -f "$expected_file" ]]; then
        if [[ "$UPDATE_EXPECTED" == "1" ]]; then
            # Generate expected file
            run_nagzen "$test_file" "$expected_file" "$with_templates"
            printf "${YELLOW}NEW ${NC} %-${NAME_WIDTH}s %s\n" "$test_name" "Created expected file"
            ((SKIPPED++))
            return 0
        else
            printf "${YELLOW}SKIP${NC} %-${NAME_WIDTH}s %s\n" "$test_name" "No .expected file (run with UPDATE_EXPECTED=1)"
            ((SKIPPED++))
            return 0
        fi
    fi

    # Start timing
    local start_time=$(date +%s%3N)

    # Run nagzen
    local actual_file="$WORK_DIR/${test_name}.actual"
    run_nagzen "$test_file" "$actual_file" "$with_templates"
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

    # Check for expected error (file starts with # EXPECT_ERROR)
    local expect_error=0
    if head -5 "$test_file" | grep -q '^# EXPECT_ERROR'; then
        expect_error=1
    fi

    # Validate exit code
    if [[ "$expect_error" == "1" && "$exit_code" == "0" ]]; then
        printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Expected error but got success" "$elapsed_str"
        ((FAILED++))
        return 1
    elif [[ "$expect_error" == "0" && "$exit_code" != "0" ]]; then
        printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Unexpected error (exit $exit_code)" "$elapsed_str"
        # Show stderr (error messages) prominently first
        if [[ -n "$NAGZEN_STDERR" ]]; then
            echo -e "  ${RED}Error:${NC}"
            echo "$NAGZEN_STDERR" | sed 's/^/  /'
        fi
        ((FAILED++))
        return 1
    fi

    # Compare output with expected
    local diff_file="$WORK_DIR/${test_name}.diff"
    if ! diff -u <(normalize_output "$expected_file") <(normalize_output "$actual_file") > "$diff_file" 2>&1; then
        # Output differs
        if [[ "$UPDATE_EXPECTED" == "1" ]]; then
            cp "$actual_file" "$expected_file"
            printf "${YELLOW}UPD ${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Updated expected file" "$elapsed_str"
            ((PASSED++))
            return 0
        fi

        printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Output mismatch" "$elapsed_str"

        # Show diff
        local diff_lines=$(wc -l < "$diff_file")
        if [[ "$VERBOSE" == "1" ]] || [[ $diff_lines -le 30 ]]; then
            echo -e "  ${CYAN}Diff:${NC}"
            # Colorize diff output
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

    # Optionally validate with nagios -v
    if [[ "$VALIDATE_NAGIOS" == "1" && "$expect_error" == "0" && "$skip_nagios" == "0" ]]; then
        local nagios_result
        nagios_result=$(validate_nagios "$actual_file" "$WORK_DIR")
        local nagios_exit=$?

        if [[ $nagios_exit -eq 1 ]]; then
            printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Nagios validation failed" "$elapsed_str"
            echo -e "  ${RED}Nagios errors:${NC}"
            echo "$nagios_result" | sed 's/^/  /'
            ((FAILED++))
            return 1
        elif [[ $nagios_exit -eq 2 ]]; then
            # Skip validation (nagios not available)
            :
        fi
    fi

    # Validate assertions (if any) - requires --nagios flag and nagios binary
    if [[ "$VALIDATE_NAGIOS" == "1" && "$expect_error" == "0" && "$skip_nagios" == "0" ]]; then
        local assert_result
        assert_result=$(validate_assertions "$test_file" "$actual_file" "$WORK_DIR")
        local assert_exit=$?

        if [[ $assert_exit -eq 1 ]]; then
            printf "${RED}FAIL${NC} %-${NAME_WIDTH}s %s ${CYAN}(%s)${NC}\n" "$test_name" "Assertion failed" "$elapsed_str"
            echo -e "  ${RED}Assertions:${NC}"
            echo "$assert_result" | sed 's/^/  /'
            ((FAILED++))
            return 1
        elif [[ $assert_exit -eq 2 ]]; then
            # Skip (nagios not available but assertions exist)
            :
        fi
    fi

    # Success
    printf "${GREEN}PASS${NC} %-${NAME_WIDTH}s ${CYAN}(%s)${NC}\n" "$test_name" "$elapsed_str"
    ((PASSED++))
    return 0
}

# Print usage
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [TEST_NAME...]

Nagzen configuration generator test runner.

Options:
  -v, --verbose         Show detailed diff output for failures
  -u, --update          Update/create .expected files from actual output
  -n, --nagios          Validate generated config with nagios -v
  -h, --help            Show this help

Environment variables:
  VERBOSE=1             Same as --verbose
  UPDATE_EXPECTED=1     Same as --update
  VALIDATE_NAGIOS=1     Same as --nagios
  NAGIOS_BIN=/path      Path to nagios binary (default: /usr/sbin/nagios)
  NAME_WIDTH=50         Test name column width
  DIFF_TOOL=diff        Diff tool to use

Test file markers (in first 5 lines):
  # SKIP [reason]       Skip this test
  # EXPECT_ERROR        Test should fail (exit non-zero)
  # WITH_TEMPLATES      Load all templates before running test
  # SKIP_NAGIOS         Skip nagios -v validation for this test

Assertions (anywhere in file, requires --nagios):
  # ASSERT service:host:svc:attr=value   Verify resolved service attribute
  # ASSERT host:hostname:attr=value      Verify resolved host attribute
  # ASSERT !service:host:svc:            Verify service does NOT exist

Examples:
  $0                              # Run all tests
  $0 001-basic-host               # Run specific test
  $0 -v                           # Verbose mode
  $0 -u                           # Update expected files
  $0 -u 010-new-test              # Create expected file for new test

EOF
    exit 0
}

# Main entry point
main() {
    echo -e "${BOLD}Nagzen Configuration Generator Tests${NC}"
    echo ""

    # Check nagzen script exists
    if [[ ! -f "$NAGZEN_SCRIPT" ]]; then
        echo -e "${RED}FAIL${NC} nagzen script not found: $NAGZEN_SCRIPT"
        exit 1
    fi

    # Find test files
    local test_files=()
    if [[ $# -gt 0 ]]; then
        for arg in "$@"; do
            if [[ -f "$CASES_DIR/$arg.cfg" ]]; then
                test_files+=("$CASES_DIR/$arg.cfg")
            elif [[ -f "$arg" ]]; then
                test_files+=("$arg")
            elif [[ -f "$arg.cfg" ]]; then
                test_files+=("$arg.cfg")
            else
                echo -e "${RED}FAIL${NC} Test not found: $arg"
            fi
        done
    else
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find "$CASES_DIR" -name '*.cfg' -print0 2>/dev/null | sort -z)
    fi

    if [[ ${#test_files[@]} -eq 0 ]]; then
        echo -e "${YELLOW}No test files found in $CASES_DIR${NC}"
        echo "Create test files as: cases/XXX-test-name.cfg"
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
        -n|--nagios)
            VALIDATE_NAGIOS=1
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
