#!/usr/bin/env python3
import random
import datetime
import os

# -------------------------------
# CONFIGURATION PARAMETERS
# -------------------------------
NUM_ARTISTS = 60
NUM_BANDS = 25
NUM_STAGES = 35
NUM_LOCATIONS = 6
NUM_FESTIVALS = 12
NUM_EVENTS_PER_FESTIVAL = 1
NUM_PERFORMANCES_PER_EVENT = 12
NUM_ATTENDEES = 180
NUM_TICKETS = 240
NUM_REVIEWS = 40
NUM_STAFF = 100

GENRE_IDS = list(range(1, 11))
SUBGENRE_IDS = list(range(1, 31))
STAFF_ROLES = {
    'security': 1,
    'support': 2,
    'sound_engineer': 3,
    'light_technician': 4,
    'stagehand': 5,
    'medic': 6,
    'cleaning': 7,
    'backstage_assistant': 8
}

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def random_date(start, end):
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + datetime.timedelta(seconds=random_seconds)

def get_dummy_url():
    return "https://example.com/image.png"

def get_dummy_caption():
    return "Example Caption"

def sanitize(text):
    return text.replace("'", "''")

def write_datalist_txt():
    datalist_lines = [
        "Data Generation Summary\n",
        "=======================\n",
        "This file documents the configuration of the synthetic data generated for populating the Pulse University Festival database.\n",
        "\nParameters:\n-----------",
        f"NUM_ARTISTS = {NUM_ARTISTS}",
        f"NUM_BANDS = {NUM_BANDS}",
        f"NUM_STAGES = {NUM_STAGES}",
        f"NUM_LOCATIONS = {NUM_LOCATIONS}",
        f"NUM_FESTIVALS = {NUM_FESTIVALS}",
        f"NUM_EVENTS_PER_FESTIVAL = {NUM_EVENTS_PER_FESTIVAL}",
        f"NUM_PERFORMANCES_PER_EVENT = {NUM_PERFORMANCES_PER_EVENT}",
        f"NUM_ATTENDEES = {NUM_ATTENDEES}",
        f"NUM_TICKETS = {NUM_TICKETS}",
        f"NUM_STAFF = {NUM_STAFF}",
        f"NUM_REVIEWS = {NUM_REVIEWS}",
        ""
    ]

    # Go three levels up: data_generation → code → project root
    root_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "..",  # data_generation
        "..",  # code
        ".."   # project root
    ))

    datalist_path = os.path.join(root_dir, "docs", "organization", "datalist.txt")
    os.makedirs(os.path.dirname(datalist_path), exist_ok=True)

    with open(datalist_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(datalist_lines))

# -------------------------------
# MAIN FUNCTION
# -------------------------------
def main():
    write_datalist_txt()
    sql = []
    today = datetime.date.today()

    # 1. Locations
    locations = []
    for i in range(1, NUM_LOCATIONS + 1):
        sql.append(
            f"INSERT INTO Location (street_name, street_number, zip_code, city, country, continent_id, latitude, longitude, image, caption) VALUES "
            f"('Street_{i}', '{random.randint(1,200)}', '{random.randint(10000,99999)}', 'City_{i}', 'Country_{i}', {random.randint(1,6)}, "
            f"{round(random.uniform(-90,90),6)}, {round(random.uniform(-180,180),6)}, '{get_dummy_url()}', '{get_dummy_caption()}');"
        )
        locations.append(i)

    # 2. Festivals
    festivals = []
    for i in range(1, NUM_FESTIVALS + 1):
        fest_year = today.year - NUM_FESTIVALS + i
        start_date = today + datetime.timedelta(days=30 * i) if i <= 2 else today - datetime.timedelta(days=365 * (NUM_FESTIVALS - i + 1))
        end_date = start_date + datetime.timedelta(days=random.randint(1, 3))
        sql.append(
            f"INSERT INTO Festival (fest_year, name, start_date, end_date, image, caption, loc_id) VALUES "
            f"({fest_year}, 'Festival_{i}', '{start_date}', '{end_date}', '{get_dummy_url()}', '{get_dummy_caption()}', {random.choice(locations)});"
        )
        festivals.append(fest_year)

    # 3. Stages
    stages = []
    for i in range(1, NUM_STAGES + 1):
        sql.append(
            f"INSERT INTO Stage (name, capacity, image, caption) VALUES "
            f"('Stage_{i}', {random.randint(100, 500)}, '{get_dummy_url()}', '{get_dummy_caption()}');"
        )
        stages.append(i)

    # 4. Events
    events = []
    for i, fest_year in enumerate(festivals, start=1):
        stage_id = random.choice(stages)
        sql.append(
            f"INSERT INTO Event (title, is_full, image, caption, fest_year, stage_id) VALUES "
            f"('Event_{fest_year}', {random.choice(['TRUE', 'FALSE'])}, '{get_dummy_url()}', '{get_dummy_caption()}', {fest_year}, {stage_id});"
        )
        events.append((i, stage_id))

    # 5. Performances
    perf_id = 1
    perf_ids = []
    base_time = datetime.datetime.combine(today, datetime.time(18, 0))
    for event_id, stage_id in events:
        for seq in range(1, NUM_PERFORMANCES_PER_EVENT + 1):
            dt = base_time + datetime.timedelta(minutes=seq * 60)
            duration = random.randint(30, 180)
            break_duration = "NULL" if seq == NUM_PERFORMANCES_PER_EVENT else str(random.randint(5, 30))
            sql.append(
                f"INSERT INTO Performance (type_id, datetime, duration, break_duration, stage_id, event_id, sequence_number) VALUES "
                f"({random.randint(1, 5)}, '{dt}', {duration}, {break_duration}, {stage_id}, {event_id}, {seq});"
            )
            perf_ids.append((perf_id, event_id))
            perf_id += 1

    # 6. Artists + Genres
    artists = []
    for i in range(1, NUM_ARTISTS + 1):
        dob = datetime.date(1970 + random.randint(0, 30), random.randint(1, 12), random.randint(1, 28))
        nickname = f"'Nick_{i}'" if random.random() < 0.5 else "NULL"
        webpage = "'https://example.com'" if random.random() < 0.5 else "NULL"
        instagram = "'@example'" if random.random() < 0.5 else "NULL"
        sql.append(
            f"INSERT INTO Artist (first_name, last_name, nickname, date_of_birth, webpage, instagram, image, caption) VALUES "
            f"('{sanitize(f'ArtistFirst_{i}')}', '{sanitize(f'ArtistLast_{i}')}', {nickname}, '{dob}', {webpage}, {instagram}, "
            f"'{get_dummy_url()}', '{get_dummy_caption()}');"
        )
        artists.append(i)
        for g in random.sample(GENRE_IDS, k=random.randint(1, 2)):
            sql.append(f"INSERT INTO Artist_Genre (artist_id, genre_id) VALUES ({i}, {g});")
        for sg in random.sample(SUBGENRE_IDS, k=random.randint(1, 2)):
            sql.append(f"INSERT INTO Artist_SubGenre (artist_id, sub_genre_id) VALUES ({i}, {sg});")

    # 7. Bands + Members + Genres
    bands = []
    for i in range(1, NUM_BANDS + 1):
        fdate = datetime.date(2000 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28))
        webpage = "'https://example.com'" if random.random() < 0.5 else "NULL"
        instagram = "'@bandexample'" if random.random() < 0.5 else "NULL"
        sql.append(
            f"INSERT INTO Band (name, formation_date, webpage, instagram, image, caption) VALUES "
            f"('{sanitize(f'Band_{i}')}', '{fdate}', {webpage}, {instagram}, '{get_dummy_url()}', '{get_dummy_caption()}');"
        )
        bands.append(i)
        members = random.sample(artists, k=random.randint(2, 4))
        for m in members:
            sql.append(f"INSERT INTO Band_Member (band_id, artist_id) VALUES ({i}, {m});")
        for g in random.sample(GENRE_IDS, k=random.randint(1, 2)):
            sql.append(f"INSERT INTO Band_Genre (band_id, genre_id) VALUES ({i}, {g});")
        for sg in random.sample(SUBGENRE_IDS, k=random.randint(1, 2)):
            sql.append(f"INSERT INTO Band_SubGenre (band_id, sub_genre_id) VALUES ({i}, {sg});")

    # 8. Performance links
    for perf_id, event_id in perf_ids:
        if random.random() < 0.5:
            sql.append(f"INSERT INTO Performance_Artist (perf_id, artist_id) VALUES ({perf_id}, {random.choice(artists)});")
        else:
            sql.append(f"INSERT INTO Performance_Band (perf_id, band_id) VALUES ({perf_id}, {random.choice(bands)});")

    # 9. Attendees
    attendees = []
    for i in range(1, NUM_ATTENDEES + 1):
        dob = datetime.date(1980 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28))
        phone = f"+30{random.randint(1000000000,9999999999)}"
        email = f"attendee{i}@example.com"
        sql.append(
            f"INSERT INTO Attendee (first_name, last_name, date_of_birth, phone_number, email) VALUES "
            f"('AttendeeFirst_{i}', 'AttendeeLast_{i}', '{dob}', '{phone}', '{email}');"
        )
        attendees.append(i)

    # 10. Tickets
    ticket_combos = set()
    for _ in range(NUM_TICKETS * 2):
        if len(ticket_combos) >= NUM_TICKETS:
            break
        att = random.choice(attendees)
        ev = random.randint(1, len(events))
        if (att, ev) in ticket_combos:
            continue
        ticket_combos.add((att, ev))
        sql.append(
            f"INSERT INTO Ticket (type_id, purchase_date, cost, method_id, ean_number, status_id, attendee_id, event_id) VALUES "
            f"({random.randint(1, 5)}, '{today - datetime.timedelta(days=random.randint(1, 100))}', {round(random.uniform(20, 200), 2)}, "
            f"{random.randint(1, 3)}, {random.randint(1000000000000, 9999999999999)}, {random.randint(1, 3)}, {att}, {ev});"
        )

    # 11. Reviews
    for _ in range(NUM_REVIEWS):
        att = random.choice(attendees)
        perf = random.choice(perf_ids)[0]
        sql.append(
            f"INSERT INTO Review (interpretation, sound_and_visuals, stage_presence, organization, overall, attendee_id, perf_id) VALUES "
            f"({random.randint(1,5)}, {random.randint(1,5)}, {random.randint(1,5)}, {random.randint(1,5)}, {random.randint(1,5)}, {att}, {perf});"
        )

    # 12. Staff
    for i in range(1, NUM_STAFF + 1):
        dob = datetime.date(1975 + random.randint(0, 30), random.randint(1, 12), random.randint(1, 28))
        role_id = random.randint(1, len(STAFF_ROLES))
        exp_id = random.randint(1, 5)
        sql.append(
            f"INSERT INTO Staff (first_name, last_name, date_of_birth, role_id, experience_id, image, caption) VALUES "
            f"('StaffFirst_{i}', 'StaffLast_{i}', '{dob}', {role_id}, {exp_id}, '{get_dummy_url()}', '{get_dummy_caption()}');"
        )
        sql.append(f"INSERT INTO Works_On (staff_id, event_id) VALUES ({i}, {random.randint(1, len(events))});")

    # Write to file
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'sql', 'load.sql')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write("-- Auto-generated SQL Load Script\n\n")
        f.write('\n'.join(sql))
    print(f"✅ Data generation complete. SQL written to {out}")

# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    main()
