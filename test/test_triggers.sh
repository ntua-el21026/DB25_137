#!/bin/bash

echo "Test Triggers" > result.txt

TOTAL=0
PASSED=0
FAILED=0

run_test() {
    TEST_NUM=$1
    DESC=$2
    SQL_FILE="q${TEST_NUM}.sql"
    OUT_FILE="o${TEST_NUM}.txt"

    echo "$3" > "$SQL_FILE"
    mariadb -u root pulse_university < "$SQL_FILE" > "$OUT_FILE" 2>&1

    echo "Test $TEST_NUM - $DESC" >> result.txt
    cat "$OUT_FILE" >> result.txt
    echo "----------------------------" >> result.txt

    ((TOTAL++))
    if grep -qi "error" "$OUT_FILE"; then
        echo "❌ Test $TEST_NUM failed"
        ((FAILED++))
    else
        echo "✅ Test $TEST_NUM passed"
        ((PASSED++))
    fi
}

# ------------------ Tests ------------------

run_test 1 "Insert event" \
"INSERT INTO event (event_id, name, date, location_id) VALUES (1001, 'Trigger Test Festival', '2025-07-20', 1);"

run_test 2 "Insert staff" \
"INSERT INTO staff (staff_id, name, role) VALUES (2001, 'John Trigger', 'volunteer');"

run_test 3 "Update staff role" \
"UPDATE staff SET role = 'manager' WHERE staff_id = 2001;"

run_test 4 "Insert artist" \
"INSERT INTO artist (artist_id, name, genre) VALUES (3001, 'Trigger Artist', 'rock');"

run_test 5 "Insert band" \
"INSERT INTO band (band_id, name) VALUES (4001, 'Trigger Band');"

run_test 6 "Add artist to band" \
"INSERT INTO band_membership (artist_id, band_id) VALUES (3001, 4001);"

run_test 7 "Insert ticket" \
"INSERT INTO ticket (ticket_id, event_id, customer_name, price) VALUES (5001, 1001, 'Alice Trigger', 99.99);"

run_test 8 "Insert resale" \
"INSERT INTO resale (resale_id, ticket_id, resale_price, buyer_name) VALUES (6001, 5001, 150.00, 'Charlie Trigger');"

run_test 9 "Delete event" \
"DELETE FROM event WHERE event_id = 1001;"

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
