import random
def gen_constraint_violations():
    return [
        "-- SETUP: ensure foreign keys exist",
        "INSERT INTO Stage (stage_id, name, capacity, image, caption) VALUES (1, 'Test Stage', 100, 'https://img.com/s.jpg', 'stage');",
        "INSERT INTO Festival (fest_year, name, start_date, end_date, image, caption, loc_id) VALUES (2025, 'TestFest', '2025-06-01', '2025-06-10', 'https://img.com/f.jpg', 'fest', 1);",
        "INSERT INTO Event (event_id, title, start_dt, end_dt, image, caption, fest_year, stage_id) VALUES (1, 'TestEvent', '2025-06-10 18:00:00', '2025-06-10 22:00:00', 'https://img.com/e.jpg', 'event', 2025, 1);",
        "INSERT INTO Performance (perf_id, type_id, datetime, duration, break_duration, stage_id, event_id, sequence_number) VALUES (1, 1, '2025-06-10 19:00:00', 60, 10, 1, 1, 1);",
        "INSERT INTO Artist (artist_id, first_name, last_name, date_of_birth, image, caption) VALUES (1, 'Test', 'Artist1', '1990-01-01', 'https://img.com/a1.jpg', 'caption');",
        "INSERT INTO Artist (artist_id, first_name, last_name, date_of_birth, image, caption) VALUES (2, 'Test', 'Artist2', '1991-01-01', 'https://img.com/a2.jpg', 'caption');",

        "-- TRIGGER TEST: Solo performance with too many artists",
        "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (1, 1);",
        "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (1, 2);  -- Should fail"
    ]


def gen_attendee_queries(n=10):
    queries = []
    for _ in range(n):
        last_initial = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        queries.append(f"SELECT * FROM Attendee WHERE last_name LIKE '{last_initial}%';")
        queries.append(f"UPDATE Attendee SET phone_number = '+1234567890' WHERE attendee_id = {random.randint(1, 100)};")
        queries.append(f"DELETE FROM Attendee WHERE attendee_id = {random.randint(101, 200)};")
    return queries

def gen_staff_queries(n=10):
    queries = []
    for _ in range(n):
        role_id = random.randint(1, 8)
        queries.append(f"SELECT first_name, last_name FROM Staff WHERE role_id = {role_id};")
        queries.append(f"UPDATE Staff SET caption = 'Updated role' WHERE staff_id = {random.randint(1, 100)};")
    return queries

def gen_event_queries(n=10):
    queries = []
    for _ in range(n):
        queries.append("SELECT title, start_dt, end_dt FROM Event WHERE is_full = FALSE;")
        queries.append(f"UPDATE Event SET is_full = TRUE WHERE event_id = {random.randint(1, 50)};")
    return queries

def gen_ticket_queries(n=10):
    queries = []
    for _ in range(n):
        cost = random.randint(50, 300)
        queries.append(f"SELECT * FROM Ticket WHERE cost > {cost} ORDER BY cost DESC;")
        queries.append(f"UPDATE Ticket SET status_id = 2 WHERE ticket_id = {random.randint(1, 100)};")
        queries.append(f"DELETE FROM Ticket WHERE ticket_id = {random.randint(200, 300)};")
    return queries

def gen_performance_queries(n=10):
    queries = []
    for _ in range(n):
        queries.append(f"SELECT * FROM Performance WHERE duration BETWEEN 30 AND 120;")
        queries.append(f"SELECT a.first_name, a.last_name FROM Artist a JOIN Performance_Artist pa ON a.artist_id = pa.artist_id WHERE perf_id = {random.randint(1, 50)};")
        queries.append(f"SELECT b.name FROM Band b JOIN Performance_Band pb ON b.band_id = pb.band_id WHERE perf_id = {random.randint(1, 50)};")
    return queries

def gen_join_queries(n=10):
    queries = []
    for _ in range(n):
        queries.append(
            "SELECT f.name, e.title FROM Festival f "
            "JOIN Event e ON f.fest_year = e.fest_year "
            "WHERE e.is_full = FALSE;"
        )
        queries.append(
            "SELECT t.ticket_id, a.first_name, a.last_name FROM Ticket t "
            "JOIN Attendee a ON t.attendee_id = a.attendee_id "
            f"WHERE t.cost > {random.randint(50, 200)};"
        )
    return queries

def write_queries_to_file(filename="test_q.sql", total_per_group=10):
    with open(filename, "w") as f:
        f.write("-- Generated SQL Queries for pulse_university\n\n")

        sections = {
            "Attendees": gen_attendee_queries(total_per_group),
            "Staff": gen_staff_queries(total_per_group),
            "Events": gen_event_queries(total_per_group),
            "Tickets": gen_ticket_queries(total_per_group),
            "Performances": gen_performance_queries(total_per_group),
            "Joins and Reports": gen_join_queries(total_per_group),
            "Constraint Violations (Trigger Tests)": gen_constraint_violations()
        }

        for title, queries in sections.items():
            f.write(f"\n-- {title} --\n")
            for q in queries:
                f.write(q + "\n")

# Run the generator
if __name__ == "__main__":
    write_queries_to_file("test_q.sql", total_per_group=20)
