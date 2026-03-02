#!/bin/bash
# Test: ZTAIL_SUFFIX environment variable

TEST_DIR="$WORK_DIR/011"
mkdir -p "$TEST_DIR"

# Create test file
echo "content" > "$TEST_DIR/test.log"

# Run with custom suffix
ZTAIL_SUFFIX=mystate "$ZTAIL_SCRIPT" "$TEST_DIR/test.log" -- cat >/dev/null

echo "custom_suffix_file: $(test -f "$TEST_DIR/test.log.mystate" && echo yes || echo no)"
echo "default_suffix_file: $(test -f "$TEST_DIR/test.log.ztail" && echo yes || echo no)"
