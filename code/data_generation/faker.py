#!/usr/bin/env python3
"""
faker.py – Pulse University demo seeder (2024-2025)

• Inserts complete, trigger-safe demo data.
• Never disables foreign-key checks; instead wipes tables with DELETE + AUTO_INCREMENT = 1.
• Keeps all integrity triggers enabled.
• Guarantees ample rows for every graded SQL query
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

# ───────────────────────── HELPERS
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
    cur.execute(
        """INSERT INTO Performance
            (type_id, datetime, duration, break_duration,
            stage_id, event_id, sequence_number)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (perf_type[ptype], p_dt, dur, BREAK,
            stage_of_year[p_dt.year], ev_id, seq)
    )
    return cur.lastrowid

def reset_table(table: str) -> None:
    cur.execute(f"DELETE FROM {table}")
    cur.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")

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

# ───────────────────────── CONNECT & LUTs
cnx = mysql.connector.connect(**DB)
cnx.autocommit = False
cur = cnx.cursor(dictionary=True)

def lut(table: str, key="name", val=None):
    val = val or table.split('_')[-1] + "_id"
    cur.execute(f"SELECT {key}, {val} FROM {table}")
    return {r[key]: r[val] for r in cur.fetchall()}

continent_id = lut("Continent")
role_id      = lut("Staff_Role")
exp_id       = lut("Experience_Level")
perf_type    = lut("Performance_Type")
ticket_type  = lut("Ticket_Type")
pay_method   = lut("Payment_Method")
status_id    = lut("Ticket_Status")
genre_id     = lut("Genre")

sub_by_genre: Dict[int, List[int]] = {}
cur.execute("SELECT sub_genre_id, genre_id FROM SubGenre")
for r in cur.fetchall():
    sub_by_genre.setdefault(r["genre_id"], []).append(r["sub_genre_id"])

# safe insert into Performance_Artist
def safe_insert_artist(perf_id: int, artist_id: int, year: int) -> bool:
    """
    Try inserting into Performance_Artist.
    If the 3-year trigger (errno 1644) fires, swallow it and return False.
    """
    try:
        cur.execute(
            "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s, %s)",
            (perf_id, artist_id)
        )
        appearances[artist_id].append(year)
        return True
    except DatabaseError as e:
        if getattr(e, "errno", None) == 1644:
            return False
        raise

# safe insert into Review
def safe_insert_review(att_id: int, perf_id: int) -> bool:
    """
    Insert a Review row, but skip if:
        • errno 1644 (“Must have USED ticket to review”)
        • errno 1062 (duplicate perf_id,attendee_id)
    """
    try:
        cur.execute(
            """INSERT INTO Review
                (interpretation,sound_and_visuals,stage_presence,
                organization,overall,attendee_id,perf_id)
                VALUES (5,5,5,5,5,%s,%s)""",
            (att_id, perf_id)
        )
        return True
    except DatabaseError as e:
        if getattr(e, "errno", None) in (1644, 1062):
            return False
        raise

print("Starting DB Loading...")
# ───────────────────────── 0. EQUIPMENT & STAGE_EQUIPMENT
print("→ equipment")
for t in ("Stage_Equipment", "Equipment"):
    reset_table(t)

# Define equipment with varied placeholder images
equip_items = [
    ("PA System",     "Main sound reinforcement"),
    ("Lighting Rig",  "LED and moving heads"),
    ("Backline Kit",  "Drums, amps, keyboards"),
    ("Wireless Mics", "8-channel microphone set"),
    ("Smoke Machine", "Low-fog special effect"),
]
placeholder_bases = [
    "https://placehold.co/600x400?text=Audio",
    "https://placehold.co/600x400?text=Lights",
    "https://placehold.co/600x400?text=Backline",
    "https://placehold.co/600x400?text=Mics",
    "https://placehold.co/600x400?text=Effects",
]
for name, caption in equip_items:
    # choose a random placeholder image for variety
    img = random.choice(placeholder_bases)
    cur.execute(
        "INSERT INTO Equipment (name, image, caption) VALUES (%s, %s, %s)",
        (name, img, caption)
    )

cur.execute("SELECT equip_id FROM Equipment")
equip_ids = [r["equip_id"] for r in cur.fetchall()]

# ───────────────────────── 1. STAGES
print("→ stages")
reset_table("Stage")
stage_of_year: Dict[int, int] = {}

for yr in range(EARLIEST, LATEST + 1):
    for idx in range(1, STAGES_PER_YEAR + 1):
        # create stage label
        label = f"Main Stage {yr}" if idx == 1 else f"Stage {idx} {yr}"
        # vary capacity ±20%
        cap = random.randint(int(CAPACITY * 0.8), int(CAPACITY * 1.2))
        # generate a unique placeholder image per stage
        img = f"https://placehold.co/800x600?text={label.replace(' ', '+')}"
        # include capacity in caption for variety
        cap_caption = f"{label} – holds approx. {cap} people"
        cur.execute(
            "INSERT INTO Stage (name, capacity, image, caption) VALUES (%s, %s, %s, %s)",
            (label, cap, img, cap_caption)
        )
        sid = cur.lastrowid
        if idx == 1:
            stage_of_year[yr] = sid

        # assign each stage a random subset of equipment (2–all items)
        eq_sample = random.sample(equip_ids, random.randint(2, len(equip_ids)))
        for eq in eq_sample:
            cur.execute(
                "INSERT INTO Stage_Equipment (stage_id, equip_id) VALUES (%s, %s)",
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

# Randomize years to assign each continent first
years = list(range(EARLIEST, LATEST + 1))
random.shuffle(years)

loc_of_year: Dict[int, int] = {}
days_of_year: Dict[int, List[date]] = {}
used = set()

# 1) First 7 years: one unique city per continent
for i in range(min(7, len(years))):
    city, cc, cont, base_lat, base_lon = cities[i]
    zip_code = f"{10000 + i}"
    # no jitter for first appearance
    lat = base_lat
    lon = base_lon
    caption = f"Venue in {city}"

    yr = years[i]
    # insert Location
    cur.execute(
        """INSERT INTO Location
              (street_name, street_number, zip_code, city, country,
               continent_id, latitude, longitude, image, caption)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            "Main", "1", zip_code, city, cc,
            continent_id[cont], lat, lon,
            "https://placehold.co/600x400", caption
        )
    )
    loc_of_year[yr] = cur.lastrowid
    used.add((city, cc))

    # compute days for this festival
    day_cnt = random.randint(MIN_EVT, MAX_EVT)
    start = date(yr, 3, 1) if yr == TODAY.year else date(yr, 7, 1)
    days = [start + timedelta(d) for d in range(day_cnt)]
    days_of_year[yr] = days

    # insert Festival
    cur.execute(
        """INSERT INTO Festival
             (fest_year, name, start_date, end_date, image, caption, loc_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (
            yr, f"Pulse {yr}", days[0], days[-1],
            "https://placehold.co/600x400", f"Pulse {yr}", loc_of_year[yr]
        )
    )

# 2) Remaining years: random city with small lat/lon jitter, avoid repeats
remaining = [yr for yr in years if yr not in loc_of_year]
for i, yr in enumerate(remaining):
    # pick unused or allow reuse occasionally
    while True:
        city, cc, cont, base_lat, base_lon = random.choice(cities)
        if (city, cc) not in used or random.random() < 0.25:
            break

    zip_code = f"{11000 + i}"
    # jitter up to ±0.005 degrees and round to 6 decimal places
    lat = round(base_lat + random.uniform(-0.005, 0.005), 6)
    lon = round(base_lon + random.uniform(-0.005, 0.005), 6)
    caption = f"Venue in {city}"

    # insert Location
    cur.execute(
        """INSERT INTO Location
              (street_name, street_number, zip_code, city, country,
               continent_id, latitude, longitude, image, caption)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            "Main", "1", zip_code, city, cc,
            continent_id[cont], lat, lon,
            "https://placehold.co/600x400", caption
        )
    )
    loc_of_year[yr] = cur.lastrowid
    used.add((city, cc))

    # compute days for this festival
    day_cnt = random.randint(MIN_EVT, MAX_EVT)
    start = date(yr, 3, 1) if yr == TODAY.year else date(yr, 7, 1)
    days = [start + timedelta(d) for d in range(day_cnt)]
    days_of_year[yr] = days

    # insert Festival
    cur.execute(
        """INSERT INTO Festival
             (fest_year, name, start_date, end_date, image, caption, loc_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (
            yr, f"Pulse {yr}", days[0], days[-1],
            "https://placehold.co/600x400", f"Pulse {yr}", loc_of_year[yr]
        )
    )

# ───────────────────────── 3. EVENTS
print("→ events")
reset_table("Event")
event_of_day = {}
for yr, days in days_of_year.items():
    for d in days:
        st = datetime.combine(d, START_TIME)
        et = st + timedelta(hours=6)
        cur.execute("""INSERT INTO Event
                        (title,is_full,start_dt,end_dt,image,caption,
                        fest_year,stage_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (f"{yr} Day {(d-days[0]).days+1}", False, st, et,
                        "https://placehold.co/600x400",
                        f"Programme day {(d-days[0]).days+1}",
                        yr, stage_of_year[yr]))
        event_of_day[(yr, d)] = cur.lastrowid

# ───────────────────────── 4. STAFF & WORKS_ON (create + enforce ratios) ─────────────────────────
print("→ staff & assignments")
reset_table("Works_On")
reset_table("Staff")

import random, math
from datetime import date

# 1) Create security staff
sec_ids: List[int] = []
for n in range(N_SEC):
    cur.execute(
        """INSERT INTO Staff
             (first_name, last_name, date_of_birth, role_id,
              experience_id, image, caption)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (
            f"Sec{n}", "Guard", date(1980,1,1),
            role_id["security"], exp_id["experienced"],
            "https://placehold.co/600x400", "Security"
        )
    )
    sec_ids.append(cur.lastrowid)

# 2) Create support staff
sup_ids: List[int] = []
for n in range(N_SUP):
    cur.execute(
        """INSERT INTO Staff
             (first_name, last_name, date_of_birth, role_id,
              experience_id, image, caption)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (
            f"Sup{n}", "Crew", date(1985,1,1),
            role_id["support"], exp_id["intermediate"],
            "https://placehold.co/600x400", "Support"
        )
    )
    sup_ids.append(cur.lastrowid)

# 3) Create other (technical) staff: 5 per remaining role
other_ids: List[int] = []
other_roles = [r for r in role_id if r not in ("security","support")]
for role_name in other_roles:
    for n in range(5):
        dob = date(random.randint(1970,2000),
                   random.randint(1,12),
                   random.randint(1,28))
        cur.execute(
            """INSERT INTO Staff
                 (first_name, last_name, date_of_birth, role_id,
                  experience_id, image, caption)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                f"{role_name.title()}{n}", "Staff", dob,
                role_id[role_name], random.choice(list(exp_id.values())),
                "https://placehold.co/600x400", role_name.title()
            )
        )
        other_ids.append(cur.lastrowid)

# 4) Assign staff to each event according to stage capacity ratios
for (yr, day), ev in event_of_day.items():
    # lookup this event’s stage capacity
    cur.execute("""
        SELECT s.capacity
          FROM Event e
          JOIN Stage s ON e.stage_id = s.stage_id
         WHERE e.event_id = %s
    """, (ev,))
    cap = cur.fetchone()["capacity"]

    # compute required minima
    min_sec  = math.ceil(cap * 0.05)           # ≥5% security
    min_sup  = math.ceil(cap * 0.02)           # ≥2% support
    min_tech = max(1, math.ceil(cap / 100))    # ≥1 tech per 100 seats

    # randomly pick that many from each pool
    chosen = []
    chosen += random.sample(sec_ids,  min(min_sec,  len(sec_ids)))
    chosen += random.sample(sup_ids,  min(min_sup,  len(sup_ids)))
    chosen += random.sample(other_ids, min(min_tech, len(other_ids)))

    # insert the assignments
    for sid in chosen:
        cur.execute(
            "INSERT INTO Works_On (staff_id, event_id) VALUES (%s,%s)",
            (sid, ev)
        )

# ───────────────────────── 5. ARTISTS & BANDS
print("→ artists & bands")
for t in ("Performance_Artist", "Performance_Band", "Band_Member",
          "Artist_SubGenre", "Artist_Genre",
          "Band_SubGenre", "Band_Genre", "Band", "Artist"):
    reset_table(t)

artist_ids, all_gen = [], list(genre_id.keys())
def pick_gen(i): return ["Rock", "Pop"] if i % 5 == 0 else random.sample(all_gen, 2)

# ─── Age Distribution Control: 65% < 30 years, 35% ≥ 30 years ───
YOUNG_RATIO = 0.65
young_cutoff = date.today().replace(year=date.today().year - 30)
num_young = int(N_ART * YOUNG_RATIO)
num_older = N_ART - num_young

def random_birthdate(young=True):
    # Generate a date of birth for young or older artist
    if young:
        start = young_cutoff
        end = date.today() - timedelta(days=365 * 18)  # at least 18 years old
    else:
        start = date(1950, 1, 1)
        end = young_cutoff - timedelta(days=1)
    delta = end.toordinal() - start.toordinal()
    return date.fromordinal(start.toordinal() + random.randint(0, delta))

# ─── Insert Artists ───
for i in range(N_ART):
    is_young = i < num_young  # First 65% will be < 30
    dob = random_birthdate(young=is_young)
    cur.execute("""INSERT INTO Artist
                    (first_name, last_name, date_of_birth,
                     webpage, instagram, image, caption)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (f"Artist{i}", "Lastname", dob,
                 "https://example.com", f"@artist{i}",
                 "https://placehold.co/600x400", "Performer"))
    aid = cur.lastrowid
    artist_ids.append(aid)
    for g in pick_gen(i):
        cur.execute("INSERT INTO Artist_Genre (artist_id, genre_id) VALUES (%s, %s)",
                    (aid, genre_id[g]))
        cur.execute("INSERT INTO Artist_SubGenre (artist_id, sub_genre_id) VALUES (%s, %s)",
                    (aid, random.choice(sub_by_genre[genre_id[g]])))

# ─── Insert Bands ───
band_ids, pool = [], artist_ids[:]
random.shuffle(pool)
for b in range(N_BAND):
    cur.execute("""INSERT INTO Band
                    (name, formation_date,
                     webpage, instagram, image, caption)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (f"Band{b}", date(2010, 1, 1),
                 "https://example.com", f"@band{b}",
                 "https://placehold.co/600x400", "Band"))
    bid = cur.lastrowid
    band_ids.append(bid)
    members = [pool.pop() for _ in range(random.randint(2, 4))]
    for m in members:
        cur.execute("INSERT INTO Band_Member (band_id, artist_id) VALUES (%s, %s)", (bid, m))
    cur.execute("SELECT genre_id FROM Artist_Genre WHERE artist_id = %s", (members[0],))
    for row in cur.fetchall():
        gid = row["genre_id"]
        cur.execute("INSERT INTO Band_Genre (band_id, genre_id) VALUES (%s, %s)", (bid, gid))
        cur.execute("INSERT INTO Band_SubGenre (band_id, sub_genre_id) VALUES (%s, %s)",
                    (bid, random.choice(sub_by_genre[gid])))

# ───────────────────────── 6. PERFORMANCES (robust booking + init-cap 15) ─────────────────────────
print("→ performances")
reset_table("Performance")

# maximum initial performances per artist
MAX_INIT_PERF = 13

# Track each artist’s festival-year history (for the 3-year limit)
# appearances[aid] = list of years they’ve been scheduled
appearances: Dict[int, List[int]] = {aid: [] for aid in artist_ids}
perf_ids_of_event: Dict[int, List[int]] = {}

# 6.1 – regular booking (80% band / 20% solo), but cap each artist at 15 total
for (yr, day), ev in event_of_day.items():
    n = random.randint(MIN_PERF, MAX_PERF)
    perf_ids_of_event[ev] = []
    for seq in range(1, n + 1):
        pid = add_perf(ev, day, seq, n)
        perf_ids_of_event[ev].append(pid)

        # leave slot 1 alone for later warm-ups
        if seq == 1:
            continue

        # try booking a band (80%), skipping any band with a maxed-out member
        if random.random() < 0.80:
            for _ in range(30):
                bid = random.choice(band_ids)
                cur.execute("SELECT artist_id FROM Band_Member WHERE band_id=%s", (bid,))
                members = [r["artist_id"] for r in cur.fetchall()]

                # enforce the 15-performance cap
                if any(len(appearances[m]) >= MAX_INIT_PERF for m in members):
                    continue

                if not all(ok_seq(appearances[m], yr) for m in members):
                    continue

                try:
                    cur.execute(
                        "INSERT INTO Performance_Band (perf_id, band_id) VALUES (%s, %s)",
                        (pid, bid)
                    )
                    for m in members:
                        appearances[m].append(yr)
                    break
                except DatabaseError as e:
                    if e.errno == 1644:  # staffing / overlap trigger
                        continue
                    raise
            continue

        # fallback: solo, skipping any artist who’s already at 15
        for _ in range(100):
            aid = random.choice(artist_ids)
            if len(appearances[aid]) >= MAX_INIT_PERF:
                continue
            if not ok_seq(appearances[aid], yr):
                continue
            try:
                cur.execute(
                    "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s, %s)",
                    (pid, aid)
                )
                appearances[aid].append(yr)
                break
            except DatabaseError as e:
                if e.errno in (1062, 1644):  # duplicate or trigger
                    continue
                raise

# 6.2 – expanded Q3 warm-up seeding: 4 days × 8 artists × each year, but cap at 15
for yr in sorted(days_of_year.keys()):
    days = days_of_year[yr][:4]                          # first 4 days
    artists_for_year = random.sample(artist_ids, min(8, len(artist_ids)))
    for artist in artists_for_year:
        # skip if already at cap
        if len(appearances[artist]) >= MAX_INIT_PERF:
            continue

        for day in days:
            ev = event_of_day[(yr, day)]
            # find or create the slot-1 performance
            cur.execute(
                "SELECT perf_id FROM Performance WHERE event_id=%s AND sequence_number=1",
                (ev,),
            )
            row = cur.fetchone()
            if row:
                pid = row["perf_id"]
            else:
                pid = add_perf(ev, day, 1, MAX_PERF)

            # insert the warm-up artist if under the cap
            if len(appearances[artist]) < MAX_INIT_PERF:
                try:
                    cur.execute(
                        "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s, %s)",
                        (pid, artist),
                    )
                    appearances[artist].append(yr)
                except DatabaseError as e:
                    # ignore duplicate or 3-year-limit errors
                    if e.errno not in (1062, 1644):
                        raise

# ───────────────────────── 7. ATTENDEES • TICKETS • REVIEWS
print("→ attendees, tickets, reviews")
for t in ("Review", "Ticket", "Attendee"):
    reset_table(t)

# fetch all ticket-type ids and locate VIP
cur.execute("SELECT type_id, name FROM Ticket_Type")
type_rows = cur.fetchall()
vip_type  = next(r["type_id"] for r in type_rows if r["name"].lower() == "vip")
other_ids = [r["type_id"] for r in type_rows if r["type_id"] != vip_type]

# create attendees
attendees: List[int] = []
for i in range(N_ATT):
    cur.execute(
        "INSERT INTO Attendee (first_name, last_name, date_of_birth, email) "
        "VALUES (%s,%s,%s,%s)",
        (f"Att{i}", "User", date(2000, 1, 1), f"att{i}@mail.com")
    )
    attendees.append(cur.lastrowid)

special_a, special_b = attendees[:2]

ean_num = 10**11
def next_ean() -> int:
    """Return a fresh EAN-13 complying number each call."""
    global ean_num
    ean_num += 1
    return ean13(ean_num)

# tickets per event
for ev, perfs in perf_ids_of_event.items():
    # load event info
    cur.execute(
        "SELECT start_dt, end_dt, fest_year FROM Event WHERE event_id=%s", (ev,)
    )
    ev_start, ev_end, fy = cur.fetchone().values()
    is_future = ev_end.date() >= TODAY

    # who already holds a ticket?
    cur.execute("SELECT attendee_id FROM Ticket WHERE event_id=%s", (ev,))
    bought = {r["attendee_id"] for r in cur.fetchall()}

    # up to 80 new buyers (exclude the two specials)
    pool = [a for a in attendees[2:] if a not in bought]
    buyers = random.sample(pool, min(80, len(pool)))

    vip_cap   = math.ceil(CAPACITY * 0.10)
    gen_share = len(other_ids)

    for idx, aid in enumerate(buyers):
        # enforce VIP cap
        t_id = vip_type if idx < vip_cap else other_ids[(idx - vip_cap) % gen_share]

        # choose status
        if fy > TODAY.year:
            status = status_id["active"] if random.random() < 0.85 else status_id["on offer"]
        else:
            status = (
                status_id["active"] if is_future
                else (status_id["used"] if random.random() < 0.80 else status_id["unused"])
            )

        try:
            cur.execute(
                """INSERT INTO Ticket
                        (type_id, purchase_date, cost, method_id, ean_number,
                         status_id, attendee_id, event_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    t_id,
                    ev_start.date() - timedelta(days=30),
                    200 if t_id == vip_type else 100,
                    pay_method["credit card"],
                    next_ean(),
                    status,
                    aid,
                    ev,
                ),
            )
        except MySQLError as e:
            # ignore duplicate or trigger-raised errors (VIP cap ⇒ errno 1644)
            if getattr(e, "errno", None) not in (1062, 1644):
                raise

    # generate reviews for each used‐ticket holder
    cur.execute(
        "SELECT attendee_id FROM Ticket WHERE event_id=%s AND status_id=%s",
        (ev, status_id["used"])
    )
    used_holders = [r["attendee_id"] for r in cur.fetchall()]

    for perf in perfs:
        for att in used_holders:
            # random chance to review (~70%)
            if random.random() < 0.7:
                scores = [random.randint(1,5) for _ in range(5)]
                try:
                    cur.execute(
                        """INSERT INTO Review
                             (interpretation, sound_and_visuals, stage_presence,
                              organization, overall, attendee_id, perf_id)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (*scores, att, perf)
                    )
                except MySQLError as e:
                    # ignore duplicates or other trigger skips
                    if getattr(e, "errno", None) != 1062:
                        raise

# ───────────────────────── 8. GUARANTEE GRADED QUERY COVERAGE
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

for gname in target_genres:
    gid  = genre_id[gname]
    cnt0 = perf_cnt(pair_years[0], gid)
    cnt1 = perf_cnt(pair_years[1], gid)
    target = max(cnt0, cnt1, MIN_PAIR_CNT)

    for yr, current in zip(pair_years, (cnt0, cnt1)):
        need = target - current
        if need <= 0:
            continue

        cur.execute("SELECT artist_id FROM Artist_Genre WHERE genre_id = %s LIMIT 1", (gid,))
        aid = cur.fetchone()["artist_id"]
        day0 = days_of_year[yr][0]
        event_id = event_of_day[(yr, day0)]

        added = 0
        tries = 0
        while added < need and tries < need * 5:
            tries += 1
            pid = safe_add_perf(event_id, day0, MAX_PERF)
            if pid is None:
                break
            if safe_insert_artist(pid, aid, yr):
                added += 1

# 8.2 Q6: ensure attendee 1 (special_a) has a USED ticket for every 2024–25 event
for (yr, _), ev in event_of_day.items():
    if yr not in (2024, 2025):
        continue

    # skip if already has any ticket for this event
    cur.execute(
        "SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s",
        (special_a, ev)
    )
    if cur.fetchone():
        continue

    # purchase the day before the event, status MUST be 'used'
    cur.execute("SELECT start_dt FROM Event WHERE event_id=%s", (ev,))
    ev_date = cur.fetchone()["start_dt"].date()
    purchase_date = ev_date - timedelta(days=1)

    cur.execute("""INSERT INTO Ticket
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
                    special_a,
                    ev
                )
    )

# 8.3 Q2: insert 10 extra Jazz artists
jazz_id   = genre_id["Jazz"]
jazz_subs = sub_by_genre[jazz_id]
for i in range(10):
    name = f"Jazzman{i}"
    cur.execute("""INSERT INTO Artist
                    (first_name,last_name,date_of_birth,
                    webpage,instagram,image,caption)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (name, "Solo", date(1990,1,1),
                    "https://example.com", f"@{name}",
                    "https://placehold.co/600x400", "Jazz artist"))
    aid = cur.lastrowid
    cur.execute("INSERT INTO Artist_Genre (artist_id,genre_id) VALUES (%s,%s)", (aid, jazz_id))
    cur.execute("INSERT INTO Artist_SubGenre (artist_id,sub_genre_id) VALUES (%s,%s)",
                (aid, random.choice(jazz_subs)))

# 8.4 Q4: add two reviews per Performance of artist_id=1 by attendee 1
cur.execute("""
    SELECT pa.perf_id, p.event_id
        FROM Performance_Artist pa
        JOIN Performance p USING (perf_id)
        WHERE pa.artist_id = 1
""")
for row in cur.fetchall():
    pid = row["perf_id"]
    ev  = row["event_id"]

    # ensure special_a has a USED ticket for this event
    cur.execute("SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s AND status_id=%s",
                (special_a, ev, status_id["used"]))
    if not cur.fetchone():
        cur.execute("SELECT start_dt FROM Event WHERE event_id=%s", (ev,))
        pd = cur.fetchone()["start_dt"].date() - timedelta(days=1)
        cur.execute("""INSERT INTO Ticket
                        (type_id,purchase_date,cost,method_id,ean_number,
                        status_id,attendee_id,event_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (ticket_type["general"], pd, 90,
                        pay_method["debit card"], next_ean(),
                        status_id["used"], special_a, ev))
    for _ in range(2):
        safe_insert_review(special_a, pid)

# 8.5 Q6 fallback – ensure ≥4 tickets in 2024 for attendee 1
cur.execute("SELECT COUNT(*) AS c FROM Ticket WHERE attendee_id=%s AND YEAR(purchase_date)=2024",
            (special_a,))
if cur.fetchone()["c"] < 4:
    for (yr, _), ev in sorted(event_of_day.items()):
        if yr != 2024:
            continue
        cur.execute("SELECT start_dt FROM Event WHERE event_id=%s", (ev,))
        pd = cur.fetchone()["start_dt"].date() - timedelta(days=1)
        cur.execute("""INSERT INTO Ticket
                        (type_id,purchase_date,cost,method_id,ean_number,
                        status_id,attendee_id,event_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (ticket_type["general"], pd, 90,
                        pay_method["debit card"], next_ean(),
                        status_id["used"], special_a, ev))
        if cur.rowcount >= 4:
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
    pid = row["perf_id"]
    ev  = row["event_id"]
    for att in (special_a, special_b):
        cur.execute("SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s AND status_id=%s",
                    (att, ev, status_id["used"]))
        if not cur.fetchone():
            cur.execute("SELECT start_dt FROM Event WHERE event_id=%s", (ev,))
            pd = cur.fetchone()["start_dt"].date() - timedelta(days=1)
            cur.execute("""INSERT INTO Ticket
                            (type_id,purchase_date,cost,method_id,ean_number,
                            status_id,attendee_id,event_id)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (ticket_type["general"], pd, 90,
                            pay_method["debit card"], next_ean(),
                            status_id["used"], att, ev))
        safe_insert_review(att, pid)

# 8.7 Q9: seed many attendees with >3 performances in a single year
from collections import defaultdict

# collect events per year
events_by_year: Dict[int, List[int]] = defaultdict(list)
for (yr, _), ev in event_of_day.items():
    events_by_year[yr].append(ev)

# choose 50 attendees (skip specials)
q9_attendees = attendees[2:52]  # next 50 attendees
for att in q9_attendees:
    for yr, ev_list in events_by_year.items():
        if len(ev_list) < 4:
            continue  # need at least 4 events to seed
        # pick 4 distinct events in this year
        chosen = random.sample(ev_list, 4)
        for ev in chosen:
            # skip if ticket already exists
            cur.execute("SELECT 1 FROM Ticket WHERE attendee_id=%s AND event_id=%s", (att, ev))
            if cur.fetchone():
                continue

            # check event capacity
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
                continue  # skip this event if full

            # get event date for purchase logic
            cur.execute("SELECT start_dt FROM Event WHERE event_id=%s", (ev,))
            ev_date = cur.fetchone()["start_dt"].date()
            purchase_date = ev_date - timedelta(days=1)

            # insert used ticket so attendee counts for Q9
            cur.execute("""INSERT INTO Ticket
                            (type_id, purchase_date, cost, method_id, ean_number,
                             status_id, attendee_id, event_id)
                           VALUES (%s,      %s,            %s,   %s,        %s,
                                   %s,       %s,           %s)""",
                        (
                            ticket_type["general"],
                            purchase_date,
                            100,
                            pay_method["debit card"],
                            next_ean(),
                            status_id["used"],
                            att,
                            ev
                        )
            )

# ───────────────────────── 8.8 Q3 FALLBACK CHECK

for year in sorted(days_of_year.keys())[-4:]:
    # find the 3 warm-up perf_ids for that year
    cur.execute("""
        SELECT p.perf_id
          FROM Performance p
          JOIN Event e ON p.event_id = e.event_id
         WHERE e.fest_year=%s
           AND p.sequence_number=1
         ORDER BY p.datetime
         LIMIT 3
    """, (year,))
    warm_pids = [r["perf_id"] for r in cur.fetchall()]
    if len(warm_pids) < 3:
        continue

    # pick the same 4 artists we used above
    # (you could store them in a list when you seeded in Section 6)
    q3_artists = random.sample(artist_ids, 4)

    for aid in q3_artists:
        # count how many warm-ups this artist already has that year
        cur.execute("""
            SELECT COUNT(*) AS c
              FROM Performance_Artist pa
              JOIN Performance p USING(perf_id)
              JOIN Event e       ON p.event_id = e.event_id
             WHERE pa.artist_id=%s
               AND p.sequence_number=1
               AND e.fest_year=%s
        """, (aid, year))
        have = cur.fetchone()["c"]
        # insert into whichever slots they’re missing
        for pid in warm_pids[: max(0, 3 - have)]:
            try:
                cur.execute(
                    "INSERT IGNORE INTO Performance_Artist (perf_id, artist_id) VALUES (%s,%s)",
                    (pid, aid)
                )
            except mysql.connector.errors.DatabaseError:
                pass

# ───────────────────────── 8.9. Q5: Tie ≥6 by fully squeezing events ─────────────────────────

# 1) find current max performance_count among <30 artists
cur.execute("""
    SELECT COUNT(*) AS cnt
      FROM View_Artist_Performance_Rating v
      JOIN Artist a ON v.artist_id = a.artist_id
     WHERE TIMESTAMPDIFF(YEAR,a.date_of_birth,CURDATE()) < 30
  GROUP BY v.artist_id
  ORDER BY cnt DESC
  LIMIT 1
""")
max_cnt = (cur.fetchone() or {}).get("cnt", 0)

# 2) pick the six artists ranked 2–7
cur.execute("""
    SELECT a.artist_id
      FROM Artist a
 LEFT JOIN Performance_Artist pa ON a.artist_id = pa.artist_id
     WHERE TIMESTAMPDIFF(YEAR,a.date_of_birth,CURDATE()) < 30
  GROUP BY a.artist_id
  ORDER BY COUNT(pa.perf_id) DESC
  LIMIT 6 OFFSET 1
""")
tie_artists = [r["artist_id"] for r in cur.fetchall()]

# 3) how many more slots each needs
need = {}
for aid in tie_artists:
    cur.execute("SELECT COUNT(*) AS c FROM Performance_Artist WHERE artist_id=%s", (aid,))
    need[aid] = max_cnt - cur.fetchone()["c"]

# helper: map event_id→day, and event→year
day_of_event = {ev: day for (yr, day), ev in event_of_day.items()}
def event_to_year(ev):
    cur.execute("SELECT fest_year FROM Event WHERE event_id=%s", (ev,))
    return cur.fetchone()["fest_year"]

# 4) build one finite shuffled list of free (year,day)
free_slots = [
    (yr, d)
    for yr in days_of_year
    for d in days_of_year[yr]
    if (yr, d) not in event_of_day
]
random.shuffle(free_slots)

group_id = 1
# 5) band-up while ≥2 artists still need slots
while True:
    group = [a for a, cnt in need.items() if cnt > 0]
    if len(group) < 2:
        break

    # create a new tie-band
    cur.execute(
        "INSERT INTO Band (name, image, caption) VALUES (%s,%s,%s)",
        (f"Q5_TieBand{group_id}", "https://placehold.co/600x400", "Tie-band")
    )
    bid = cur.lastrowid
    for a in group:
        cur.execute(
            "INSERT INTO Band_Member (band_id, artist_id) VALUES (%s,%s)",
            (bid, a)
        )

    added = False
    # 5a) Squeeze **existing** events fully
    for ev, day in day_of_event.items():
        # how many slots already?
        cur.execute("SELECT COUNT(*) AS c FROM Performance WHERE event_id=%s", (ev,))
        filled = cur.fetchone()["c"]
        # while we still need at least one round and event isn't full
        while filled < MAX_PERF and min(need[a] for a in group) > 0:
            pid = safe_add_perf(ev, day, MAX_PERF)  # enforces no-overlap/breaks :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
            if not pid:
                break
            # assign our band (fans out to members) :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
            cur.execute(
                "INSERT INTO Performance_Band (perf_id, band_id) VALUES (%s,%s)",
                (pid, bid)
            )
            perf_ids_of_event[ev].append(pid)
            filled += 1
            for a in group:
                need[a] -= 1
            added = True

    # 5b) Then squeeze **new** events on free days
    while free_slots and min(need[a] for a in group) > 0:
        yr, day = free_slots.pop()
        st = datetime.combine(day, START_TIME)
        et = st + timedelta(hours=6)
        cur.execute("""
            INSERT INTO Event
              (title,is_full,start_dt,end_dt,image,caption,fest_year,stage_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            f"Extra Tie Event {group_id}", False, st, et,
            "https://placehold.co/600x400","Squeezed", yr, stage_of_year[yr]
        ))
        ev_new = cur.lastrowid
        event_of_day[(yr, day)] = ev_new
        day_of_event[ev_new] = day
        perf_ids_of_event[ev_new] = []

        # fill up to MAX_PERF slots
        for _ in range(min(MAX_PERF, min(need[a] for a in group))):
            pid = safe_add_perf(ev_new, day, MAX_PERF)
            if not pid:
                break
            cur.execute(
                "INSERT INTO Performance_Band (perf_id, band_id) VALUES (%s,%s)",
                (pid, bid)
            )
            perf_ids_of_event[ev_new].append(pid)
            for a in group:
                need[a] -= 1
            added = True

    if not added:
        # nothing more to do
        break

    group_id += 1

# 6) if one artist left, give them squeezed solos
left = [a for a, cnt in need.items() if cnt > 0]
if left:
    aid = left[0]
    rem = need[aid]

    # 6a) existing events
    for ev, day in day_of_event.items():
        if rem <= 0:
            break
        cur.execute("SELECT COUNT(*) AS c FROM Performance WHERE event_id=%s", (ev,))
        filled = cur.fetchone()["c"]
        while filled < MAX_PERF and rem > 0:
            pid = safe_add_perf(ev, day, MAX_PERF)
            if not pid:
                break
            cur.execute(
                "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s,%s)",
                (pid, aid)
            )
            perf_ids_of_event[ev].append(pid)
            filled += 1
            rem -= 1

    # 6b) new events
    while rem > 0 and free_slots:
        yr, day = free_slots.pop()
        st = datetime.combine(day, START_TIME)
        et = st + timedelta(hours=6)
        cur.execute("""
            INSERT INTO Event
              (title,is_full,start_dt,end_dt,image,caption,fest_year,stage_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            "Extra Solo Event", False, st, et,
            "https://placehold.co/600x400","Solo-squeeze", yr, stage_of_year[yr]
        ))
        ev_new = cur.lastrowid
        event_of_day[(yr, day)] = ev_new
        day_of_event[ev_new] = day
        perf_ids_of_event[ev_new] = []

        while rem > 0 and len(perf_ids_of_event[ev_new]) < MAX_PERF:
            pid = safe_add_perf(ev_new, day, MAX_PERF)
            if not pid:
                break
            cur.execute(
                "INSERT INTO Performance_Artist (perf_id, artist_id) VALUES (%s,%s)",
                (pid, aid)
            )
            perf_ids_of_event[ev_new].append(pid)
            rem -= 1

# ───────────────────────── 9. RESALE QUEUES FOR FUTURE FESTIVALS ─────────────────────────
print("→ resale queues for future festivals")

# list of future events
future_events = [ev for (yr, _), ev in event_of_day.items() if yr > TODAY.year]

# all ticket types
cur.execute("SELECT type_id FROM Ticket_Type")
all_types = [r["type_id"] for r in cur.fetchall()]

ACTIVE = status_id["active"]

for ev in future_events:
    # --- 9.a First-wave OFFERS (up-to-10, never >½ of active tickets)
    cur.execute("""
        SELECT ticket_id, attendee_id, type_id
          FROM Ticket
         WHERE event_id = %s AND status_id = %s
    """, (ev, ACTIVE))
    tickets = cur.fetchall()
    random.shuffle(tickets)
    if not tickets:
        continue

    max_pairs = min(10, len(tickets) // 2)
    offers1   = tickets[:max_pairs]
    for row in offers1:
        cur.execute(
            "INSERT INTO Resale_Offer (ticket_id, event_id, seller_id) VALUES (%s,%s,%s)",
            (row["ticket_id"], ev, row["attendee_id"])
        )
    offered_types = {r["type_id"] for r in offers1}

    # --- 9.b Interests (exactly max_pairs rows) – some match now, some stay pending
    cur.execute("SELECT attendee_id FROM Ticket WHERE event_id=%s", (ev,))
    holders = {r["attendee_id"] for r in cur.fetchall()}
    pool    = [a for a in attendees if a not in holders]
    buyers  = random.sample(pool, max_pairs)

    half = max_pairs // 2
    for i, buyer in enumerate(buyers):
        if i < half:
            # request an offered type ⇒ immediate trigger-match
            typ = random.choice(list(offered_types))
        else:
            # request a non-offered type ⇒ stays pending
            not_off = [t for t in all_types if t not in offered_types]
            typ     = random.choice(not_off or all_types)

        cur.execute(
            "INSERT INTO Resale_Interest (buyer_id, event_id) VALUES (%s,%s)",
            (buyer, ev)
        )
        req = cur.lastrowid
        cur.execute(
            "INSERT INTO Resale_Interest_Type (request_id, type_id) VALUES (%s,%s)",
            (req, typ)
        )

    # --- 9.c Second-wave OFFERS – only match half of the remaining pending interests
    cur.execute("""
        SELECT ri.request_id, rit.type_id
          FROM Resale_Interest ri
          JOIN Resale_Interest_Type rit USING(request_id)
         WHERE ri.event_id = %s
    """, (ev,))
    pending = cur.fetchall()  # list of dicts with request_id & type_id
    to_match = random.sample(pending, math.ceil(len(pending) / 2))

    for row in to_match:
        typ = row["type_id"]
        # find an ACTIVE ticket of this type that isn't already on offer
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
        r2 = cur.fetchone()
        if not r2:
            continue
        cur.execute(
            "INSERT INTO Resale_Offer (ticket_id, event_id, seller_id) VALUES (%s,%s,%s)",
            (r2["ticket_id"], ev, r2["attendee_id"])
        )
        # trigger will auto-match and remove the corresponding Resale_Interest

print("→ resale seed complete: check with 'db137 viewq'")

# ───────────────────────── COMMIT & CLOSE
cnx.commit()
cur.close()
cnx.close()
print("\nDatabase successfully populated!\n")

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
