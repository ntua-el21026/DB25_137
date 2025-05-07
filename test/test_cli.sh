#!/bin/bash
# test_cli.sh – Tests db137 user commands on pulse_university

set +H  # Disable Bash history expansion (!)

# --------- Setup ---------
DB137="python3 $(dirname "$0")/../cli/db137.py"
OUTFILE="test_cli_results.txt"
mkdir -p "$(dirname "$OUTFILE")"

# Redirect all output (stdout + stderr) to the output file only
exec >"$OUTFILE" 2>&1

USER1="testuser1"
USER2="testuser2"
USER3="testuser3"
PASS='Test1234!'
NEWPASS='NewTest5678!'

TOTAL=0
PASSED=0
FAILED=0

# --------- Debug info ---------
echo "DEBUG: Entered test_cli.sh"
echo "DB137=$DB137"
which bash
echo

# --------- Helper: Run test command ---------
function test_cmd() {
    local desc="$1"
    shift
    local cmd=("$@")
    local expect_fail=0

    if [[ "$desc" == EXPECT_FAIL:* ]]; then
        desc="${desc#EXPECT_FAIL: }"
        expect_fail=1
    fi

    ((TOTAL++))
    echo "▶ $desc..."
    echo "Command: ${cmd[*]}"
    if "${cmd[@]}"; then
        if [[ "$expect_fail" -eq 1 ]]; then
            echo "[FAIL] $desc (unexpected success)"
            ((FAILED++))
        else
            echo "[PASS] $desc"
            ((PASSED++))
        fi
    else
        if [[ "$expect_fail" -eq 1 ]]; then
            echo "[PASS] $desc (expected failure)"
            ((PASSED++))
        else
            echo "[FAIL] $desc"
            ((FAILED++))
        fi
        echo "Exit code: $?"
    fi
    echo
}

# --------- Helper: Show user privileges ---------
function show_user_grants() {
    local user="$1"
    echo "▶ Current grants for $user:"
    $DB137 users list | awk -v u="$user" '
        $0 == "- " u { show = 1; print; next }
        show && $0 ~ /^  / { print; next }
        show { exit }
    '
    echo
}

# --------- Begin tests ---------
echo "========== USER COMMANDS TEST =========="
echo "Working dir: $(pwd)"
echo "Database: pulse_university"
echo "Output: $OUTFILE"
echo "========================================"
echo

test_cmd "Drop pulse_university DB" \
    $DB137 drop-db --database pulse_university --yes

test_cmd "Create pulse_university DB" \
    $DB137 create-db

test_cmd "Drop user $USER1 (if exists)" \
    $DB137 users drop $USER1 || true

test_cmd "Drop user $USER2 (if exists)" \
    $DB137 users drop $USER2 || true

test_cmd "Drop user $USER3 (if exists)" \
    $DB137 users drop $USER3 || true

test_cmd "Register $USER1 with basic privileges" \
    $DB137 users register $USER1 --password $PASS \
    --default-db pulse_university --privileges SELECT,INSERT,UPDATE,DELETE
show_user_grants $USER1

test_cmd "Register $USER2 with default privileges" \
    $DB137 users register $USER2 --password $PASS \
    --default-db pulse_university
show_user_grants $USER2

test_cmd "List all users" \
    $DB137 users list

test_cmd "Revoke INSERT from $USER1 with --show-diff" \
    $DB137 users revoke $USER1 --db pulse_university --privileges INSERT --show-diff
show_user_grants $USER1

test_cmd "Change password for $USER1" \
    $DB137 users passwd $USER1 --new-pass $NEWPASS

test_cmd "Verify login as $USER1 after password change" \
    env DB_ROOT_USER=$USER1 DB_ROOT_PASS=$NEWPASS $DB137 users whoami

test_cmd "Rename $USER1 to $USER3" \
    $DB137 users rename $USER1 $USER3
show_user_grants $USER3

test_cmd "Set default privileges for $USER3 with --show-diff" \
    $DB137 users set-defaults $USER3 --show-diff
show_user_grants $USER3

test_cmd "Grant INSERT to $USER3 with --show-diff" \
    $DB137 users grant $USER3 --db pulse_university --privileges INSERT --show-diff
show_user_grants $USER3

test_cmd "List all users after rename" \
    $DB137 users list

test_cmd "Show whoami as $USER3" \
    env DB_ROOT_USER=$USER3 DB_ROOT_PASS=$NEWPASS $DB137 users whoami

# --------- Verify access control for non-root users ---------
echo "========== ACCESS CONTROL TESTS =========="
echo

test_cmd "EXPECT_FAIL: Reject register attempt as testuser2" \
    env DB_ROOT_USER=$USER2 DB_ROOT_PASS=$PASS $DB137 users register shouldfail --password dummy --default-db pulse_university --privileges SELECT

test_cmd "EXPECT_FAIL: Reject drop attempt as testuser2" \
    env DB_ROOT_USER=$USER2 DB_ROOT_PASS=$PASS $DB137 users drop testuser3

test_cmd "EXPECT_FAIL: Reject rename attempt as testuser2 (on another user)" \
    env DB_ROOT_USER=$USER2 DB_ROOT_PASS=$PASS $DB137 users rename testuser3 eviluser

test_cmd "EXPECT_FAIL: Reject set-defaults attempt as testuser2" \
    env DB_ROOT_USER=$USER2 DB_ROOT_PASS=$PASS $DB137 users set-defaults testuser1

test_cmd "Allow testuser2 to change their own password" \
    env DB_ROOT_USER=$USER2 DB_ROOT_PASS=$PASS $DB137 users passwd $USER2 --new-pass 'Changed567!'

test_cmd "Verify login as testuser2 with new password" \
    env DB_ROOT_USER=$USER2 DB_ROOT_PASS='Changed567!' $DB137 users whoami

# --------- Cleanup ---------
test_cmd "Drop all test users" \
    $DB137 users drop-all

test_cmd "Final users list" \
    $DB137 users list

# --------- Summary ---------
echo "========================================"
echo "Tests completed."
echo "Total: $TOTAL  |  Passed: $PASSED  |  Failed: $FAILED"
echo

FAILED="${FAILED:-0}"

if [[ "$FAILED" -eq 0 ]]; then
    exit 0
else
    exit 1
fi
