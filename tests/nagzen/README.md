# Nagzen Test Suite

Automated test system for the Nagios configuration generator (nagzen).

## Overview

This system validates nagzen behavior by comparing generated output against reference files. It is inspired by the yana-core API test runner, adapted for testing Nagios configuration generation.

## Structure

```
tests/nagzen/
├── runner.sh                 # Main test script
├── README.md                 # This documentation
└── cases/                    # Test cases
    ├── XXX-name.cfg            # Source file (nagzen declarations)
    └── XXX-name.expected       # Expected output (generated Nagios objects)
```

## How it works

1. The runner sources the `nagzen` script to load functions
2. Optionally loads templates from `configs/nagzen/templates/`
3. Executes the test `.cfg` file
4. Compares output against the `.expected` file
5. Reports PASS/FAIL based on the result

## Usage

### Run all tests

```bash
./tests/nagzen/runner.sh
```

### Run a specific test

```bash
./tests/nagzen/runner.sh 001-basic-host-template
./tests/nagzen/runner.sh 100-issue-duplicate-host-reopen-template
```

### Verbose mode (show full diffs)

```bash
./tests/nagzen/runner.sh -v
# or
VERBOSE=1 ./tests/nagzen/runner.sh
```

### Create/update .expected files

```bash
./tests/nagzen/runner.sh -u
# or
UPDATE_EXPECTED=1 ./tests/nagzen/runner.sh
```

## Creating a new test

### 1. Create the test file

Create `cases/XXX-test-name.cfg`:

```bash
# Test: Short description of the test
# Additional explanations if needed

host myhost:linux --template
  service ADM-SSH
  service CPU __WARNING=80
```

### 2. Generate the .expected file

```bash
./tests/nagzen/runner.sh -u XXX-test-name
```

### 3. Review the generated content

```bash
cat cases/XXX-test-name.expected
```

### 4. Validate the test

```bash
./tests/nagzen/runner.sh XXX-test-name
```

## Special markers

Add these markers in the **first 5 lines** of the `.cfg` file:

| Marker | Description |
|--------|-------------|
| `# SKIP [reason]` | Skip this test |
| `# EXPECT_ERROR` | Test should fail (exit non-zero, e.g., `FATAL: ...`) |
| `# WITH_TEMPLATES` | Load all templates before running the test |

### Example: Test with templates

```bash
# Test: Verify inheritance from standard templates
# WITH_TEMPLATES

host myserver:linux --address=192.168.1.10
  service SWAP __WARNING=50
```

### Example: Expected error test

```bash
# Test: Verify that redefining an existing template fails
# EXPECT_ERROR
# WITH_TEMPLATES

host linux --template
  service ADM-SSH __PORT=2244
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VERBOSE` | 0 | Show full diffs |
| `UPDATE_EXPECTED` | 0 | Update .expected files |
| `NAME_WIDTH` | 50 | Test name column width |
| `XDEBUG` | 0 | Enable bash debug mode in nagzen |
| `DEBUG` | 0 | Nagzen debug level |

## Test organization

Tests are numbered by category:

| Range | Category |
|-------|----------|
| 001-099 | Basic unit tests |
| 100-199 | Bug / regression tests |

### Basic tests (001-099)

| Test | Description |
|------|-------------|
| 001-basic-host-template | Basic host template declaration |
| 002-basic-host-concrete | Concrete host declaration with address |
| 003-host-with-services | Host template with services |
| 004-service-with-custom-vars | `__CUSTOM` variables on services |
| 005-service-alias | Service aliases (display:template) |
| 006-service-disable | Service disabling with `--disable` |
| 007-host-inheritance | Multi-level inheritance chain |
| 008-concrete-host-service-override | Service override on concrete host |
| 009-host-custom-vars | `__CUSTOM` variables on hosts |
| 010-service-template-standalone | Standalone service template |

### Bug tests (100-199)

| Test | Bug | Status |
|------|-----|--------|
| 100-issue-duplicate-host-reopen-template | Cannot reopen an existing template | **Confirmed** |
| 101-issue-duplicate-host-disable-service | Cannot disable service on existing template | **Confirmed** |
| 102-issue-swap-loses-check-command | check_command loss on SWAP | Inheritance OK |
| 103-issue-nbprocess-keeps-check-command | NB-PROCESS keeps check_command | Inheritance OK |
| 104-issue-swap-vs-nbprocess-comparison | SWAP vs NB-PROCESS comparison | Same behavior |
| 105-issue-contact-groups-inheritance | contact_groups inheritance | `+` prefix preserved |
| 106-workaround-intermediate-template | Workaround with intermediate template | Works |
| 107-service-alias-inheritance-chain | Inheritance chain with alias | Works |
| 110-issue-swap-debian-hierarchy | Deep hierarchy (debian) | Correct inheritance |
| 111-issue-swap-deep-hierarchy | Multi-level hierarchy | Correct inheritance |

## CI Integration

```bash
# In a CI pipeline
./tests/nagzen/runner.sh || exit 1
```

Exit codes:
- `0`: All tests pass
- `1`: At least one test failed

## Technical notes

### Noglob handling

The nagzen script enables `set -f` (noglob) at startup. The runner must temporarily re-enable glob expansion to load templates:

```bash
set +f  # Re-enable glob expansion
tpl_files=( "$TEMPLATES_DIR"/*.cfg )
set -f  # Restore noglob
```

### Template loading

When `# WITH_TEMPLATES` is specified, the runner:

1. Loads templates in numeric order (000_, 050_, 100_, etc.)
2. Calls `host-end` after each template to finalize hosts
3. Redirects output to `/dev/null` (only internal state is preserved)
4. Then executes the test file

This simulates the behavior of `update-nagios build`.

### Output comparison

Comparison uses `diff -u` with normalization:
- Trailing whitespace removal
- Multiple blank line normalization

## Output examples

### Passing test

```
PASS 001-basic-host-template                            (2ms)
```

### Failing test

```
FAIL 007-host-inheritance                               Output mismatch (5ms)
  Diff:
  @@ -1,5 +1,5 @@
   #### _level1:_ping ####
   define host {
  -  register             0
  +  register             1
     name                 _level1
```

### Skipped test

```
SKIP 050-future-feature                                 No .expected file (run with UPDATE_EXPECTED=1)
```

## Troubleshooting

### Test fails with "Unexpected error"

Check that the test file is syntactically correct:

```bash
bash -n cases/XXX-test.cfg
```

### Templates are not loaded

Verify that `# WITH_TEMPLATES` is in the first 5 lines of the file.

### Unexpected output difference

Regenerate the .expected file and compare:

```bash
./tests/nagzen/runner.sh -u XXX-test
git diff cases/XXX-test.expected
```
