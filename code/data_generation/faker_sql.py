#!/usr/bin/env python3
"""
faker.py – Pulse University demo seeder (2024-2025)

• Inserts complete, trigger-safe demo data.
• Never disables foreign-key checks; instead wipes tables with DELETE + AUTO_INCREMENT = 1.
• Keeps all integrity triggers enabled, including the 3-year limit.
• Guarantees ample rows for every graded SQL query (Q2, Q4, Q6, Q11, Q14).
"""

from __future__ import annotations
import os
import sys
import random
import math
import subprocess
from datetime import date, datetime, time, timedelta
from typing import Dict, List

import mysql.connector
from mysql.connector import Error as MySQLError, DatabaseError
from dotenv import load_dotenv

load_dotenv()
from pathlib import Path
cli_path = Path(__file__).resolve().parents[2] / "cli" / "db137.py"

# ── Auto-run create-db from cli/db137.py ──
try:
    subprocess.run([sys.executable, str(cli_path), "create-db"], check=True)
except subprocess.CalledProcessError as e:
    print("Failed to run db137 create-db:", e)
    sys.exit(1)

# ───────────────────────── CONFIG
DB = {
    "user":               os.getenv("DB_ROOT_USER", "root"),
    "password":           os.getenv("DB_ROOT_PASS", ""),
    "host":               os.getenv("DB_HOST", "localhost"),
    "database":           os.getenv("DB_NAME", "pulse_university"),
    "port":               int(os.getenv("DB_PORT", 3306)),
    "raise_on_warnings":  True,
}

SEED                     = 42
CAPACITY                 = 100
SEC_PER_EVENT, SUP_PER_EVENT = 5, 2
MIN_EVT, MAX_EVT         = 4, 6
MIN_PERF, MAX_PERF       = 3, 6
WARM_MIN, SET_MIN, BREAK = 30, 45, 10
START_TIME               = time(18, 0)
EARLIEST, LATEST         = 2016, 2027
TODAY                    = date(2025, 5, 8)

# rubric targets
STAGES_PER_YEAR          = 3          # 3 stages × 12 yrs = 36 ≥ 30
N_ART, N_BAND            = 45, 10     # 55 performers ≥ 50
N_SEC, N_SUP, N_ATT      = 20, 10, 2000

random.seed(SEED)

# ───────────────────────── CONNECT, CURSOR & PREPARE LOAD.SQL
cnx = mysql.connector.connect(**DB)
cur = cnx.cursor(dictionary=True)

load_sql_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../sql/load.sql")
)
f = open(load_sql_path, "w", encoding="utf-8")
f.write("USE pulse_university;\n")

def write_sql(stmt: str, params: tuple = None):
    """
    Execute the statement; if it succeeds, append it to load.sql.
    Returns lastrowid for INSERTs, else None. Errors propagate to caller.
    """
    # execute first
    if params:
        cur.execute(stmt, params)
    else:
        cur.execute(stmt)
    # then write
    if params:
        parts = stmt.split("%s")
        vals = []
        for p in params:
            if isinstance(p, str):
                v = p.replace("'", "''")
                vals.append(f"'{v}'")
            elif isinstance(p, (date, datetime)):
                vals.append(f"'{p.isoformat()}'")
            elif p is None:
                vals.append("NULL")
            else:
                vals.append(str(p))
        formatted = "".join(parts[i] + vals[i] for i in range(len(vals))) + parts[-1]
    else:
        formatted = stmt
    f.write(formatted.strip() + ";\n")
    # return ID if insert
    if stmt.lstrip().upper().startswith("INSERT"):
        return cur.lastrowid
    return None

# ───────────────────────── HELPERS (unchanged)
def ean13(body12: int) -> int:
    s = str(body12).zfill(12)
    chk = (10 - sum((3 if i & 1 else 1) * int(d) for i, d in enumerate(s)) % 10) % 10
    return int(s + str(chk))

def ok_seq(years: List[int], new: int, limit: int = 3) -> bool:
    seq = sorted(set(years + [new])); run = best = 1
    for a, b in zip(seq, seq[1:]):
        run = run + 1 if b == a + 1 else 1
        best = max(best, run)
    return best <= limit

def add_perf(ev_id: int, day: date, seq: int, total: int) -> int:
    ptype = ("warm up" if seq == 1 else "headline" if seq == total else "other")
    dur   = WARM_MIN if seq == 1 else SET_MIN
    p_dt  = datetime.combine(day, START_TIME) + timedelta(minutes=(seq - 1) * (dur + BREAK))
    pid = write_sql(
        """INSERT INTO Performance
            (type_id, datetime, duration, break_duration,
             stage_id, event_id, sequence_number)
          VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (perf_type[ptype], p_dt, dur, BREAK,
         stage_of_year[p_dt.year], ev_id, seq)
    )
    return pid  # so we can track perf IDs in-memory

def reset_table(table: str) -> None:
    write_sql(f"DELETE FROM {table}")
    write_sql(f"ALTER TABLE {table} AUTO_INCREMENT = 1")

# ───────────────────────── LOOKUPS
continent_id = {}
cur.execute("SELECT name, continent_id FROM Continent")
for r in cur.fetchall():
    continent_id[r["name"]] = r["continent_id"]

role_id = {}
cur.execute("SELECT name, role_id FROM Staff_Role")
for r in cur.fetchall():
    role_id[r["name"]] = r["role_id"]

exp_id = {}
cur.execute("SELECT name, level_id FROM Experience_Level")
for r in cur.fetchall():
    exp_id[r["name"]] = r["level_id"]

perf_type = {}
cur.execute("SELECT name, type_id FROM Performance_Type")
for r in cur.fetchall():
    perf_type[r["name"]] = r["type_id"]

ticket_type = {}
cur.execute("SELECT name, type_id FROM Ticket_Type")
for r in cur.fetchall():
    ticket_type[r["name"]] = r["type_id"]

pay_method = {}
cur.execute("SELECT name, method_id FROM Payment_Method")
for r in cur.fetchall():
    pay_method[r["name"]] = r["method_id"]

status_id = {}
cur.execute("SELECT name, status_id FROM Ticket_Status")
for r in cur.fetchall():
    status_id[r["name"]] = r["status_id"]

genre_id = {}
cur.execute("SELECT name, genre_id FROM Genre")
for r in cur.fetchall():
    genre_id[r["name"]] = r["genre_id"]

sub_by_genre: Dict[int, List[int]] = {}
cur.execute("SELECT sub_genre_id, genre_id FROM SubGenre")
for r in cur.fetchall():
    sub_by_genre.setdefault(r["genre_id"], []).append(r["sub_genre_id"])

print("Starting Loading SQL Generation...")
# ───────────────────────── 0. EQUIPMENT & STAGE_EQUIPMENT
print("→ equipment")
for t in ("Stage_Equipment", "Equipment"):
    reset_table(t)

equip_items = [
    ("PA System",     "Main sound reinforcement"),
    ("Lighting Rig",  "LED and moving heads"),
    ("Backline Kit",  "Drums, amps, keyboards"),
    ("Wireless Mics", "8-channel microphone set"),
    ("Smoke Machine", "Low-fog special effect"),
]
# varied placeholder images for equipment
placeholder_bases = [
    "https://placehold.co/600x400?text=Audio",
    "https://placehold.co/600x400?text=Lights",
    "https://placehold.co/600x400?text=Backline",
    "https://placehold.co/600x400?text=Mics",
    "https://placehold.co/600x400?text=Effects",
]

equip_ids: List[int] = []
for name, caption in equip_items:
    img = random.choice(placeholder_bases)  # pick a random image for variety
    eid = write_sql(
        "INSERT INTO Equipment (name,image,caption) VALUES (%s,%s,%s)",
        (name, img, caption)
    )
    equip_ids.append(eid)

# ───────────────────────── 1. STAGES
print("→ stages")
# first delete any Events that still reference Stage.stage_id
reset_table("Event")
reset_table("Stage")
stage_of_year: Dict[int, int] = {}

for yr in range(EARLIEST, LATEST + 1):
    for idx in range(1, STAGES_PER_YEAR + 1):
        label = f"Main Stage {yr}" if idx == 1 else f"Stage {idx} {yr}"
        # vary capacity by ±20%
        cap = random.randint(int(CAPACITY * 0.8), int(CAPACITY * 1.2))
        # generate a unique placeholder image per stage
        img = f"https://placehold.co/800x600?text={label.replace(' ', '+')}"
        # include capacity in the caption
        cap_caption = f"{label} – holds approx. {cap} people"

        sid = write_sql(
            "INSERT INTO Stage (name,capacity,image,caption) VALUES (%s,%s,%s,%s)",
            (label, cap, img, cap_caption)
        )
        if idx == 1:
            stage_of_year[yr] = sid

        # assign a random subset (2–all) of equipment to this stage
        eq_sample = random.sample(equip_ids, random.randint(2, len(equip_ids)))
        for eq in eq_sample:
            write_sql(
                "INSERT INTO Stage_Equipment (stage_id,equip_id) VALUES (%s,%s)",
                (sid, eq)
            )

# ───────────────────────── 2. LOCATIONS & FESTIVALS
print("→ locations & festivals")
for t in ("Festival", "Location"):
    reset_table(t)

# Cities per continent with base coordinates
cities = [
    ("Athens",     "GR", "Europe",        37.983800,  23.727500),
    ("Berlin",     "DE", "Europe",        52.520000,  13.405000),
    ("Austin",     "US", "North America", 30.267200, -97.743100),
    ("Tokyo",      "JP", "Asia",          35.689500, 139.691700),
    ("São Paulo",  "BR", "South America", -23.550500, -46.633300),
    ("Cape Town",  "ZA", "Africa",        -33.924900,  18.424100),
    ("Melbourne",  "AU", "Oceania",       -37.813600, 144.963100),
]

# Shuffle years to assign distinct cities first
years = list(range(EARLIEST, LATEST + 1))
random.shuffle(years)

loc_of_year: Dict[int, int] = {}
days_of_year: Dict[int, List[date]] = {}
used = set()

# 1) First 7 years: one unique city per continent
for i in range(min(7, len(years))):
    city, cc, cont, base_lat, base_lon = cities[i]
    zip_code = f"{10000 + i}"
    lat = base_lat
    lon = base_lon
    caption = f"Venue in {city}"

    yr = years[i]
    lid = write_sql(
        """INSERT INTO Location
             (street_name,street_number,zip_code,city,country,
              continent_id,latitude,longitude,image,caption)
           VALUES ('Main','1',%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            zip_code, city, cc,
            continent_id[cont],
            lat, lon,
            "https://placehold.co/600x400", caption
        )
    )
    loc_of_year[yr] = lid
    used.add((city, cc))

    day_cnt = random.randint(MIN_EVT, MAX_EVT)
    start   = date(yr, 3, 1) if yr == TODAY.year else date(yr, 7, 1)
    days    = [start + timedelta(d) for d in range(day_cnt)]
    days_of_year[yr] = days

    write_sql(
        """INSERT INTO Festival
             (fest_year,name,start_date,end_date,image,caption,loc_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (
            yr, f"Pulse {yr}", days[0], days[-1],
            "https://placehold.co/600x400", f"Pulse {yr}", lid
        )
    )

# 2) Remaining years: random city with small lat/lon jitter, avoid repeats
remaining = [yr for yr in years if yr not in loc_of_year]
for i, yr in enumerate(remaining):
    while True:
        city, cc, cont, base_lat, base_lon = random.choice(cities)
        if (city, cc) not in used or random.random() < 0.25:
            break

    zip_code = f"{11000 + i}"
    lat = round(base_lat + random.uniform(-0.005, 0.005), 6)
    lon = round(base_lon + random.uniform(-0.005, 0.005), 6)
    caption = f"Venue in {city}"

    lid = write_sql(
        """INSERT INTO Location
             (street_name,street_number,zip_code,city,country,
              continent_id,latitude,longitude,image,caption)
           VALUES ('Main','1',%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            zip_code, city, cc,
            continent_id[cont],
            lat, lon,
            "https://placehold.co/600x400", caption
        )
    )
    loc_of_year[yr] = lid
    used.add((city, cc))

    day_cnt = random.randint(MIN_EVT, MAX_EVT)
    start   = date(yr, 3, 1) if yr == TODAY.year else date(yr, 7, 1)
    days    = [start + timedelta(d) for d in range(day_cnt)]
    days_of_year[yr] = days

    write_sql(
        """INSERT INTO Festival
             (fest_year,name,start_date,end_date,image,caption,loc_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (
            yr, f"Pulse {yr}", days[0], days[-1],
            "https://placehold.co/600x400", f"Pulse {yr}", lid
        )
    )

# ───────────────────────── 3. EVENTS
print("→ events")
event_of_day: Dict[tuple[int,date],int] = {}

for yr, days in days_of_year.items():
    for d in days:
        st = datetime.combine(d, START_TIME)
        et = st + timedelta(hours=6)
        eid = write_sql(
            """INSERT INTO Event
                 (title,is_full,start_dt,end_dt,image,caption,
                  fest_year,stage_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (f"{yr} Day {(d-days[0]).days+1}", False, st, et,
             "https://placehold.co/600x400",
             f"Programme day {(d-days[0]).days+1}",
             yr, stage_of_year[yr])
        )
        event_of_day[(yr, d)] = eid

# ───────────────────────── 4. STAFF & WORKS_ON
print("→ staff & assignments")
for t in ("Works_On", "Staff"):
    reset_table(t)

# 1) Create security staff
sec_ids: List[int] = []
for n in range(N_SEC):
    sid = write_sql(
        """INSERT INTO Staff
             (first_name, last_name, date_of_birth, role_id,
              experience_id, image, caption)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            f"Sec{n}", "Guard", date(1980, 1, 1),
            role_id["security"], exp_id["experienced"],
            "https://placehold.co/600x400", "Security"
        )
    )
    sec_ids.append(sid)

# 2) Create support staff
sup_ids: List[int] = []
for n in range(N_SUP):
    sid = write_sql(
        """INSERT INTO Staff
             (first_name, last_name, date_of_birth, role_id,
              experience_id, image, caption)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            f"Sup{n}", "Crew", date(1985, 1, 1),
            role_id["support"], exp_id["intermediate"],
            "https://placehold.co/600x400", "Support"
        )
    )
    sup_ids.append(sid)

# 3) Create other staff roles for variety
other_ids: List[int] = []
for role_name, rid in role_id.items():
    if role_name not in ("security", "support"):
        for n in range(5):  # 5 staff per other role
            # random date_of_birth between 1970 and 1995
            year = random.randint(1970, 1995)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            dob = date(year, month, day)
            exp_choice = random.choice(list(exp_id.values()))
            caption = role_name.title()
            sid = write_sql(
                """INSERT INTO Staff
                     (first_name, last_name, date_of_birth, role_id,
                      experience_id, image, caption)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    f"{role_name.replace(' ', '')}{n}", "Staff", dob,
                    rid, exp_choice,
                    "https://placehold.co/600x400", caption
                )
            )
            other_ids.append(sid)

# 4) Assign staff to events
for ev in event_of_day.values():
    # always assign required security and support
    for sid in sec_ids[:SEC_PER_EVENT]:
        write_sql("INSERT INTO Works_On (staff_id, event_id) VALUES (%s, %s)", (sid, ev))
    for sid in sup_ids[:SUP_PER_EVENT]:
        write_sql("INSERT INTO Works_On (staff_id, event_id) VALUES (%s, %s)", (sid, ev))

    # assign ~80% of other staff to each event for more coverage
    count_other = math.ceil(len(other_ids) * 0.8)
    for sid in random.sample(other_ids, count_other):
        write_sql("INSERT INTO Works_On (staff_id, event_id) VALUES (%s, %s)", (sid, ev))

# ───────────────────────── 5. ARTISTS & BANDS
print("→ artists & bands")
for t in ("Performance_Artist", "Performance_Band", "Band_Member",
          "Artist_SubGenre", "Artist_Genre",
          "Band_SubGenre", "Band_Genre", "Band", "Artist"):
    reset_table(t)

artist_ids: List[int] = []
all_gen = list(genre_id.keys())

def pick_gen(i): 
    return ["Rock", "Pop"] if i % 5 == 0 else random.sample(all_gen, 2)

# ─── Age Distribution Control: 65% < 30 years, 35% ≥ 30 years ───
YOUNG_RATIO = 0.65
young_cutoff = date.today().replace(year=date.today().year - 30)
num_young = int(N_ART * YOUNG_RATIO)
num_older = N_ART - num_young

def random_birthdate(young=True):
    # Generate a date of birth for a young or older artist
    if young:
        start = young_cutoff
        end = date.today() - timedelta(days=365 * 18)  # min 18 y.o.
    else:
        start = date(1950, 1, 1)
        end = young_cutoff - timedelta(days=1)
    delta = end.toordinal() - start.toordinal()
    return date.fromordinal(start.toordinal() + random.randint(0, delta))

# ─── Insert Artists ───
for i in range(N_ART):
    is_young = i < num_young  # First 65% will be < 30 years old
    dob = random_birthdate(young=is_young)
    aid = write_sql(
        """INSERT INTO Artist
             (first_name, last_name, date_of_birth,
              webpage, instagram, image, caption)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (f"Artist{i}", "Lastname", dob,
         "https://example.com", f"@artist{i}",
         "https://placehold.co/600x400", "Performer")
    )
    artist_ids.append(aid)
    for g in pick_gen(i):
        write_sql(
            "INSERT INTO Artist_Genre (artist_id, genre_id) VALUES (%s, %s)",
            (aid, genre_id[g])
        )
        write_sql(
            "INSERT INTO Artist_SubGenre (artist_id, sub_genre_id) VALUES (%s, %s)",
            (aid, random.choice(sub_by_genre[genre_id[g]]))
        )

# ─── Insert Bands ───
band_ids: List[int] = []
pool = artist_ids[:]
random.shuffle(pool)

for b in range(N_BAND):
    bid = write_sql(
        """INSERT INTO Band
             (name, formation_date,
              webpage, instagram, image, caption)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (f"Band{b}", date(2010, 1, 1),
         "https://example.com", f"@band{b}",
         "https://placehold.co/600x400", "Band")
    )
    band_ids.append(bid)

    members = [pool.pop() for _ in range(random.randint(2, 4))]
    for m in members:
        write_sql("INSERT INTO Band_Member (band_id, artist_id) VALUES (%s, %s)", (bid, m))

    # mirror your original: read back each genre of artist #0
    cur.execute("SELECT genre_id FROM Artist_Genre WHERE artist_id = %s", (members[0],))
    for row in cur.fetchall():
        gid = row["genre_id"]
        write_sql("INSERT INTO Band_Genre (band_id, genre_id) VALUES (%s, %s)", (bid, gid))
        write_sql(
            "INSERT INTO Band_SubGenre (band_id, sub_genre_id) VALUES (%s, %s)",
            (bid, random.choice(sub_by_genre[gid]))
        )

# ───────────────────────── 6. PERFORMANCES (robust booking)
print("→ performances")
reset_table("Performance")

appearances: Dict[int, List[int]] = {aid: [] for aid in artist_ids}
perf_ids_of_event: Dict[int, List[int]] = {}
warm_artist = artist_ids[0]

for (yr, day), ev in event_of_day.items():
    n = random.randint(MIN_PERF, MAX_PERF)
    perf_ids_of_event[ev] = []
    for seq in range(1, n + 1):
        pid = add_perf(ev, day, seq, n)
        perf_ids_of_event[ev].append(pid)

        # warm-ups: Artist #0 opens first 3 days of 2024
        if yr == 2024 and seq == 1 and (day - days_of_year[yr][0]).days < 3:
            try:
                write_sql(
                    "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s, %s)",
                    (pid, warm_artist)
                )
                appearances[warm_artist].append(yr)
            except DatabaseError as e:
                # swallow the 3-year-limit trigger; re-raise anything else
                if getattr(e, "errno", None) != 1644:
                    raise
            continue

        booked = False
        # 80% band, 20% solo
        if random.random() < 0.80:
            for _ in range(30):
                bid = random.choice(band_ids)
                cur.execute("SELECT artist_id FROM Band_Member WHERE band_id = %s", (bid,))
                members = [r["artist_id"] for r in cur.fetchall()]
                if not all(ok_seq(appearances[m], yr) for m in members):
                    continue
                try:
                    write_sql(
                        "INSERT INTO Performance_Band (perf_id, band_id) VALUES (%s, %s)",
                        (pid, bid)
                    )
                    for m in members:
                        appearances[m].append(yr)
                    booked = True
                    break
                except DatabaseError as e:
                    if getattr(e, "errno", None) == 1644:
                        continue
                    raise
        if booked:
            continue

        # solo booking: try up to 100 artists
        for _ in range(100):
            aid = random.choice(artist_ids)
            if not ok_seq(appearances[aid], yr):
                continue
            try:
                write_sql(
                    "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s, %s)",
                    (pid, aid)
                )
                appearances[aid].append(yr)
                break
            except DatabaseError as e:
                if getattr(e, "errno", None) == 1644:
                    continue
                raise

# ───────────────────────── 7. ATTENDEES • TICKETS • REVIEWS
print("→ attendees, tickets, reviews")
for t in ("Review", "Ticket", "Attendee"):
    reset_table(t)

# Create attendees
attendees: List[int] = []
for i in range(N_ATT):
    aid = write_sql(
        "INSERT INTO Attendee (first_name, last_name, date_of_birth, email) VALUES (%s,%s,%s,%s)",
        (f"Att{i}", "User", date(2000, 1, 1), f"att{i}@mail.com")
    )
    attendees.append(aid)

special_a, special_b = attendees[:2]
ean_num = 10**11
def next_ean() -> int:
    global ean_num
    ean_num += 1
    return ean13(ean_num)

# Precompute ticket-type IDs
cur.execute("SELECT type_id, name FROM Ticket_Type")
type_map = {r["name"].lower(): r["type_id"] for r in cur.fetchall()}
vip_type = type_map["vip"]
other_types = [tid for name, tid in type_map.items() if name != "vip"]

# Generate tickets and reviews
for ev, perfs in perf_ids_of_event.items():
    # fetch event metadata
    cur.execute("SELECT start_dt, end_dt, fest_year FROM Event WHERE event_id=%s", (ev,))
    ev_start, ev_end, fy = cur.fetchone().values()
    is_future = ev_end.date() >= TODAY

    # who already has a ticket
    cur.execute("SELECT attendee_id FROM Ticket WHERE event_id=%s", (ev,))
    bought = {r["attendee_id"] for r in cur.fetchall()}

    pool = [a for a in attendees[2:] if a not in bought]
    buyers = random.sample(pool, min(80, len(pool)))

    vip_cap = math.ceil(CAPACITY * 0.10)
    for idx, aid in enumerate(buyers):
        # assign type with VIP cap
        t_id = vip_type if idx < vip_cap else other_types[(idx - vip_cap) % len(other_types)]
        status = (
            status_id["active"] if fy > TODAY.year and random.random() < 0.85 else
            status_id["on offer"] if fy > TODAY.year else
            status_id["active"] if is_future else
            (status_id["used"] if random.random() < 0.80 else status_id["unused"])
        )
        cost = 200 if t_id == vip_type else 100

        try:
            write_sql(
                """INSERT INTO Ticket
                     (type_id, purchase_date, cost, method_id, ean_number,
                      status_id, attendee_id, event_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    t_id,
                    ev_start.date() - timedelta(days=30),
                    cost,
                    pay_method["credit card"],
                    next_ean(),
                    status,
                    aid,
                    ev,
                )
            )
        except DatabaseError as e:
            # ignore duplicates and VIP cap trigger (errno 1062 or 1644)
            if getattr(e, "errno", None) not in (1062, 1644):
                raise

    # collect all used-ticket holders for reviews
    cur.execute(
        "SELECT attendee_id FROM Ticket WHERE event_id=%s AND status_id=%s",
        (ev, status_id["used"])
    )
    used_holders = [r["attendee_id"] for r in cur.fetchall()]

    # for each performance, randomly generate reviews
    for pid in perfs:
        for aid in used_holders:
            if random.random() < 0.7:  # ~70% chance to leave a review
                scores = [random.randint(1, 5) for _ in range(5)]
                try:
                    write_sql(
                        """INSERT INTO Review
                             (interpretation, sound_and_visuals, stage_presence,
                              organization, overall, attendee_id, perf_id)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (*scores, aid, pid)
                    )
                except DatabaseError as e:
                    # ignore duplicate-review errors
                    if getattr(e, "errno", None) != 1062:
                        raise

# ───────────────────────── 8. GUARANTEE GRADED QUERY COVERAGE ─────────────────────────
print("→ guarantee graded query coverage")

# 8.1 Q14: Rock, Pop, Jazz each have ≥3 performances in 2024 & 2025
pair_years    = (2024, 2025)
target_genres = ["Rock", "Pop", "Jazz"]
MIN_PAIR_CNT  = 3

def perf_cnt(year, gid):
    cur.execute("""
        SELECT COUNT(*) AS c
          FROM Performance p
          JOIN Event            e  ON e.event_id     = p.event_id
          JOIN Performance_Artist pa ON pa.perf_id   = p.perf_id
          JOIN Artist_Genre      ag ON ag.artist_id = pa.artist_id
         WHERE e.fest_year = %s AND ag.genre_id = %s
    """, (year, gid))
    return cur.fetchone()["c"]

def safe_add_perf(ev_id: int, day: date, total: int) -> int | None:
    """
    Try up to 10 random slots for this event/day.
    Skip any that trigger “Stage already booked” (errno 1644).
    Returns the new perf_id, or None if none succeeded.
    """
    for _ in range(10):
        seq = random.randint(2, total - 1)
        try:
            return add_perf(ev_id, day, seq, total)
        except DatabaseError as e:
            if getattr(e, "errno", None) == 1644:
                continue
            raise
    return None

for gname in target_genres:
    gid  = genre_id[gname]
    cnt0 = perf_cnt(pair_years[0], gid)
    cnt1 = perf_cnt(pair_years[1], gid)
    target = max(cnt0, cnt1, MIN_PAIR_CNT)

    for yr, current in zip(pair_years, (cnt0, cnt1)):
        need = target - current
        if need <= 0:
            continue

        cur.execute(
            "SELECT artist_id FROM Artist_Genre WHERE genre_id = %s LIMIT 1",
            (gid,)
        )
        aid  = cur.fetchone()["artist_id"]
        day0 = days_of_year[yr][0]
        ev0  = event_of_day[(yr, day0)]

        added = tries = 0
        while added < need and tries < need * 5:
            tries += 1
            # use safe_add_perf (catches “stage already booked” trigger)
            pid = safe_add_perf(ev0, day0, MAX_PERF)
            if pid is None:
                break
            try:
                write_sql(
                    "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s, %s)",
                    (pid, aid)
                )
                appearances[aid].append(yr)
                added += 1
            except DatabaseError:
                continue

# 8.2 Q6: ensure attendee 1 (special_a) has a USED ticket for every 2024–25 event
for (yr, _), ev in event_of_day.items():
    if yr not in (2024, 2025):
        continue

    cur.execute(
        "SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s",
        (special_a, ev)
    )
    if cur.fetchone():
        continue

    cur.execute(
        "SELECT start_dt FROM Event WHERE event_id=%s",
        (ev,)
    )
    ev_date = cur.fetchone()["start_dt"].date()
    pd = ev_date - timedelta(days=1)

    write_sql(
        """INSERT INTO Ticket
             (type_id, purchase_date, cost, method_id, ean_number,
              status_id, attendee_id, event_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            ticket_type["general"], pd, 90,
            pay_method["debit card"], next_ean(),
            status_id["used"], special_a, ev
        )
    )

# 8.3 Q2: insert 10 extra Jazz artists
jazz_id   = genre_id["Jazz"]
jazz_subs = sub_by_genre[jazz_id]
for i in range(10):
    name = f"Jazzman{i}"
    aid = write_sql(
        """INSERT INTO Artist
             (first_name,last_name,date_of_birth,
              webpage,instagram,image,caption)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (name, "Solo", date(1990,1,1),
         "https://example.com", f"@{name}",
         "https://placehold.co/600x400", "Jazz artist")
    )
    write_sql(
        "INSERT INTO Artist_Genre (artist_id,genre_id) VALUES (%s,%s)",
        (aid, jazz_id)
    )
    write_sql(
        "INSERT INTO Artist_SubGenre (artist_id,sub_genre_id) VALUES (%s,%s)",
        (aid, random.choice(jazz_subs))
    )

# 8.4 Q4: two reviews per Performance of artist_id=1 by attendee 1
cur.execute("""
    SELECT pa.perf_id, p.event_id
      FROM Performance_Artist pa
      JOIN Performance p USING (perf_id)
     WHERE pa.artist_id = 1
""")
for row in cur.fetchall():
    pid = row["perf_id"]; ev = row["event_id"]

    # ensure special_a has a USED ticket for this event
    cur.execute(
        "SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s AND status_id=%s",
        (special_a, ev, status_id["used"])
    )
    if not cur.fetchone():
        cur.execute(
            "SELECT start_dt FROM Event WHERE event_id=%s",
            (ev,)
        )
        pd = cur.fetchone()["start_dt"].date() - timedelta(days=1)
        write_sql(
            """INSERT INTO Ticket
                 (type_id,purchase_date,cost,method_id,ean_number,
                  status_id,attendee_id,event_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                ticket_type["general"], pd, 90,
                pay_method["debit card"], next_ean(),
                status_id["used"], special_a, ev
            )
        )

    # attempt two reviews, skipping duplicates or trigger errors
    for _ in range(2):
        try:
            write_sql(
                """INSERT INTO Review
                     (interpretation,sound_and_visuals,stage_presence,
                      organization,overall,attendee_id,perf_id)
                   VALUES (5,5,5,5,5,%s,%s)""",
                (special_a, pid)
            )
        except DatabaseError as e:
            if getattr(e, "errno", None) not in (1062, 1644):
                raise

# 8.5 Q6 fallback – ensure ≥4 tickets in 2024 for attendee 1
cur.execute(
    "SELECT COUNT(*) AS c FROM Ticket WHERE attendee_id=%s AND YEAR(purchase_date)=2024",
    (special_a,)
)
if cur.fetchone()["c"] < 4:
    for (yr, _), ev in sorted(event_of_day.items()):
        if yr != 2024:
            continue
        cur.execute(
            "SELECT start_dt FROM Event WHERE event_id=%s",
            (ev,)
        )
        pd = cur.fetchone()["start_dt"].date() - timedelta(days=1)
        write_sql(
            """INSERT INTO Ticket
                 (type_id,purchase_date,cost,method_id,ean_number,
                  status_id,attendee_id,event_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                ticket_type["general"], pd, 90,
                pay_method["debit card"], next_ean(),
                status_id["used"], special_a, ev
            )
        )
        break

# 8.6 Q11: attendees 1 & 2 each review 5 performances of artist 1
cur.execute("""
    SELECT pa.perf_id, p.event_id
      FROM Performance_Artist pa
      JOIN Performance p USING (perf_id)
     WHERE pa.artist_id = 1
     LIMIT 5
""")
for row in cur.fetchall():
    pid, ev = row["perf_id"], row["event_id"]
    for att in (special_a, special_b):
        cur.execute(
            "SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s AND status_id=%s",
            (att, ev, status_id["used"])
        )
        if not cur.fetchone():
            cur.execute(
                "SELECT start_dt FROM Event WHERE event_id=%s",
                (ev,)
            )
            pd = cur.fetchone()["start_dt"].date() - timedelta(days=1)
            write_sql(
                """INSERT INTO Ticket
                     (type_id,purchase_date,cost,method_id,ean_number,
                      status_id,attendee_id,event_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    ticket_type["general"], pd, 90,
                    pay_method["debit card"], next_ean(),
                    status_id["used"], att, ev
                )
            )
        try:
            write_sql(
                """INSERT INTO Review
                     (interpretation,sound_and_visuals,stage_presence,
                      organization,overall,attendee_id,perf_id)
                   VALUES (5,5,5,5,5,%s,%s)""",
                (att, pid)
            )
        except DatabaseError as e:
            if getattr(e, "errno", None) not in (1062, 1644):
                raise

# 8.7 Q9: seed many attendees with >3 performances in a single year
from collections import defaultdict

# Collect events per year
events_by_year: Dict[int, List[int]] = defaultdict(list)
for (yr, _), ev in event_of_day.items():
    events_by_year[yr].append(ev)

# Use 50 ordinary attendees (excluding special_a/b)
q9_attendees = attendees[2:52]

for att in q9_attendees:
    for yr, ev_list in events_by_year.items():
        if len(ev_list) < 4:
            continue  # skip if not enough events

        # pick 4 events from this year (same count)
        chosen = random.sample(ev_list, 4)

        for ev in chosen:
            # check if already bought
            cur.execute("SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s", (att, ev))
            if cur.fetchone():
                continue

            # check if capacity reached
            cur.execute("""
                SELECT s.capacity, COUNT(*) AS sold
                  FROM Event e
                  JOIN Stage s ON e.stage_id = s.stage_id
                  JOIN Ticket t ON t.event_id = e.event_id
                 WHERE e.event_id = %s
                 GROUP BY s.capacity
            """, (ev,))
            row = cur.fetchone()
            if not row or row["sold"] >= row["capacity"]:
                continue  # skip full events

            # get event date
            cur.execute("SELECT start_dt FROM Event WHERE event_id = %s", (ev,))
            ev_date = cur.fetchone()["start_dt"].date()
            purchase_date = ev_date - timedelta(days=1)

            # insert used ticket
            write_sql(
                """INSERT INTO Ticket
                     (type_id, purchase_date, cost, method_id, ean_number,
                      status_id, attendee_id, event_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    ticket_type["general"],
                    purchase_date,
                    90,
                    pay_method["debit card"],
                    next_ean(),
                    status_id["used"],
                    att,
                    ev,
                )
            )

# ───────────────────────── 9. RESALE QUEUES FOR FUTURE FESTIVALS ─────────────────────────
print("→ resale queues for future festivals")

# list of future events
future_events = [ev for (yr, _), ev in event_of_day.items() if yr > TODAY.year]

# every ticket_type id
all_types = list(ticket_type.values())
ACTIVE    = status_id["active"]

for ev in future_events:
    # pull active tickets
    cur.execute("""
        SELECT ticket_id, attendee_id, type_id
          FROM Ticket
         WHERE event_id = %s AND status_id = %s
    """, (ev, ACTIVE))
    tickets = cur.fetchall()
    random.shuffle(tickets)
    if not tickets:
        continue

    # 9.a First-wave OFFERS (up to 10, never >½ of active tickets)
    max_pairs = min(10, len(tickets) // 2)
    offers1   = tickets[:max_pairs]
    for row in offers1:
        write_sql(
            "INSERT INTO Resale_Offer (ticket_id,event_id,seller_id) VALUES (%s,%s,%s)",
            (row["ticket_id"], ev, row["attendee_id"])
        )
    offered_types = {r["type_id"] for r in offers1}

    # 9.b INTERESTS (exactly max_pairs rows) – some matching now, some later
    cur.execute("SELECT attendee_id FROM Ticket WHERE event_id=%s", (ev,))
    holders = {r["attendee_id"] for r in cur.fetchall()}
    pool   = [a for a in attendees if a not in holders]
    buyers = random.sample(pool, max_pairs)

    pending_types: List[int] = []
    for i, buyer in enumerate(buyers):
        if i < max_pairs // 2:
            # request a currently offered type
            typ = random.choice(list(offered_types))
        else:
            # request a type not yet offered
            not_off = [t for t in all_types if t not in offered_types]
            typ = random.choice(not_off or all_types)

        write_sql(
            "INSERT INTO Resale_Interest (buyer_id,event_id) VALUES (%s,%s)",
            (buyer, ev)
        )
        req = cur.lastrowid
        write_sql(
            "INSERT INTO Resale_Interest_Type (request_id,type_id) VALUES (%s,%s)",
            (req, typ)
        )
        pending_types.append(typ)

    # 9.c Second-wave OFFERS – match only half of the pending interests
    match_count = max(1, len(pending_types) // 2)
    to_match = random.sample(pending_types, match_count)
    for typ in to_match:
        cur.execute("""
            SELECT ticket_id, attendee_id
              FROM Ticket
             WHERE event_id = %s
               AND type_id  = %s
               AND status_id = %s
               AND NOT EXISTS (
                   SELECT 1 FROM Resale_Offer ro
                    WHERE ro.ticket_id = Ticket.ticket_id
               )
             LIMIT 1
        """, (ev, typ, ACTIVE))
        row = cur.fetchone()
        if not row:
            continue
        write_sql(
            "INSERT INTO Resale_Offer (ticket_id,event_id,seller_id) VALUES (%s,%s,%s)",
            (row["ticket_id"], ev, row["attendee_id"])
        )
        # existing trigger will log the match into Resale_Match_Log

print("→ resale seed complete: check with 'db137 viewq'")


# ───────────────────────── CLEANUP
f.close()
cnx.commit()
cur.close()
cnx.close()
print("\nAll SQL written to sql/load.sql\n")

# ───────────────────────── SUMMARY LOG TO db_data.txt
print("→ logging DB row counts to db_data.txt")

import re
from pathlib import Path

try:
    # Run db137 db-status and capture its output
    result = subprocess.run(
    [sys.executable, str(cli_path), "db-status"],
    capture_output=True, text=True, check=True
    )

    out_lines = result.stdout.splitlines()
    summary = ["Pulse University – Data Summary", "-" * 35]

    for line in out_lines:
        match = re.match(r"(\w[\w\d_]*)\s+(\d+)\s+rows", line)
        if match:
            table, count = match.groups()
            summary.append(f"{table:<24} → {count} rows")

    summary.append("-" * 35)

    output_dir = Path(__file__).resolve().parents[2] / "docs" / "organization"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "db_data.txt"
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("[OK] db_data.txt written.")

except subprocess.CalledProcessError as e:
    print("[ERROR] Failed to run db137 db-status:")
    print(e.stderr or e)
