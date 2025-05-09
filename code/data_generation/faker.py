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

# ── Auto-run create-db from cli/db137.py ──
try:
    subprocess.run(["python3", "../../cli/db137.py", "create-db"], check=True)
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

equip_items = [
    ("PA System",     "Main sound reinforcement"),
    ("Lighting Rig",  "LED and moving heads"),
    ("Backline Kit",  "Drums, amps, keyboards"),
    ("Wireless Mics", "8-channel microphone set"),
    ("Smoke Machine", "Low-fog special effect"),
]
for name, caption in equip_items:
    cur.execute(
        "INSERT INTO Equipment (name,image,caption) VALUES (%s,%s,%s)",
        (name, "https://placehold.co/600x400", caption)
    )

cur.execute("SELECT equip_id FROM Equipment")
equip_ids = [r["equip_id"] for r in cur.fetchall()]

# ───────────────────────── 1. STAGES
print("→ stages")
reset_table("Stage")
stage_of_year: Dict[int, int] = {}
for yr in range(EARLIEST, LATEST + 1):
    for idx in range(1, STAGES_PER_YEAR + 1):
        label = f"Main Stage {yr}" if idx == 1 else f"Stage {idx} {yr}"
        cur.execute(
            "INSERT INTO Stage (name,capacity,image,caption) VALUES (%s,%s,%s,%s)",
            (label, CAPACITY, "https://placehold.co/600x400", label)
        )
        sid = cur.lastrowid
        if idx == 1:
            stage_of_year[yr] = sid
        for eq in equip_ids:
            cur.execute(
                "INSERT INTO Stage_Equipment (stage_id,equip_id) VALUES (%s,%s)",
                (sid, eq)
            )

# ───────────────────────── 2. LOCATIONS & FESTIVALS
print("→ locations & festivals")
for t in ("Festival", "Location"):
    reset_table(t)

cities = [
    ("Athens","GR","Europe"), ("Austin","US","North America"),
    ("Tokyo","JP","Asia"),   ("Berlin","DE","Europe"),
    ("São Paulo","BR","South America"), ("Cape Town","ZA","Africa"),
    ("Melbourne","AU","Oceania")
]

loc_of_year, days_of_year = {}, {}
for i, yr in enumerate(range(EARLIEST, LATEST + 1)):
    city, cc, cont = random.choice(cities)
    cur.execute("""INSERT INTO Location
                        (street_name,street_number,zip_code,city,country,
                    continent_id,latitude,longitude,image,caption)
                    VALUES ('Main','1',%s,%s,%s,%s,0,0,
                            'https://placehold.co/600x400',%s)""",
                (f"{10000+i}", city, cc, continent_id[cont], f"Venue in {city}"))
    loc_of_year[yr] = cur.lastrowid

    day_cnt = random.randint(MIN_EVT, MAX_EVT)
    start   = date(yr,3,1) if yr == TODAY.year else date(yr,7,1)
    days_of_year[yr] = [start + timedelta(d) for d in range(day_cnt)]

    cur.execute("""INSERT INTO Festival
                    (fest_year,name,start_date,end_date,image,caption,loc_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (yr, f"Pulse {yr}", days_of_year[yr][0], days_of_year[yr][-1],
                    "https://placehold.co/600x400", f"Pulse {yr}", loc_of_year[yr]))

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

# ───────────────────────── 4. STAFF & WORKS_ON
print("→ staff & assignments")
for t in ("Works_On", "Staff"):
    reset_table(t)

sec_ids, sup_ids = [], []
for n in range(N_SEC):
    cur.execute("""INSERT INTO Staff
                    (first_name,last_name,date_of_birth,role_id,
                    experience_id,image,caption)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (f"Sec{n}", "Guard", date(1980,1,1),
                    role_id["security"], exp_id["experienced"],
                    "https://placehold.co/600x400", "Security"))
    sec_ids.append(cur.lastrowid)
for n in range(N_SUP):
    cur.execute("""INSERT INTO Staff
                    (first_name,last_name,date_of_birth,role_id,
                    experience_id,image,caption)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (f"Sup{n}", "Crew", date(1985,1,1),
                    role_id["support"], exp_id["intermediate"],
                    "https://placehold.co/600x400", "Support"))
    sup_ids.append(cur.lastrowid)
for ev in event_of_day.values():
    for sid in sec_ids[:SEC_PER_EVENT]:
        cur.execute("INSERT INTO Works_On (staff_id,event_id) VALUES (%s,%s)", (sid, ev))
    for sid in sup_ids[:SUP_PER_EVENT]:
        cur.execute("INSERT INTO Works_On (staff_id,event_id) VALUES (%s,%s)", (sid, ev))

# ───────────────────────── 5. ARTISTS & BANDS
print("→ artists & bands")
for t in ("Performance_Artist","Performance_Band","Band_Member",
            "Artist_SubGenre","Artist_Genre",
            "Band_SubGenre","Band_Genre","Band","Artist"):
    reset_table(t)

artist_ids, all_gen = [], list(genre_id.keys())
def pick_gen(i): return ["Rock","Pop"] if i % 5 == 0 else random.sample(all_gen, 2)

for i in range(N_ART):
    cur.execute("""INSERT INTO Artist
                    (first_name,last_name,date_of_birth,
                    webpage,instagram,image,caption)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (f"Artist{i}", "Lastname", date(1990,1,1),
                    "https://example.com", f"@artist{i}",
                    "https://placehold.co/600x400", "Performer"))
    aid = cur.lastrowid
    artist_ids.append(aid)
    for g in pick_gen(i):
        cur.execute("INSERT INTO Artist_Genre (artist_id,genre_id) VALUES (%s,%s)",
                    (aid, genre_id[g]))
        cur.execute("INSERT INTO Artist_SubGenre (artist_id,sub_genre_id) VALUES (%s,%s)",
                    (aid, random.choice(sub_by_genre[genre_id[g]])))

band_ids, pool = [], artist_ids[:]
random.shuffle(pool)
for b in range(N_BAND):
    cur.execute("""INSERT INTO Band
                    (name,formation_date,
                    webpage,instagram,image,caption)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                (f"Band{b}", date(2010,1,1),
                    "https://example.com", f"@band{b}",
                    "https://placehold.co/600x400", "Band"))
    bid = cur.lastrowid
    band_ids.append(bid)
    members = [pool.pop() for _ in range(random.randint(2,4))]
    for m in members:
        cur.execute("INSERT INTO Band_Member (band_id,artist_id) VALUES (%s,%s)", (bid, m))
    cur.execute("SELECT genre_id FROM Artist_Genre WHERE artist_id=%s", (members[0],))
    for row in cur.fetchall():
        gid = row["genre_id"]
        cur.execute("INSERT INTO Band_Genre (band_id,genre_id) VALUES (%s,%s)", (bid, gid))
        cur.execute("INSERT INTO Band_SubGenre (band_id,sub_genre_id) VALUES (%s,%s)",
                    (bid, random.choice(sub_by_genre[gid])))

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
            safe_insert_artist(pid, warm_artist, yr)
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
                cur.execute("SAVEPOINT sp_band")
                try:
                    cur.execute(
                        "INSERT INTO Performance_Band (perf_id, band_id) VALUES (%s, %s)",
                        (pid, bid)
                    )
                    for m in members:
                        appearances[m].append(yr)
                    booked = True
                    break
                except DatabaseError as e:
                    if getattr(e, "errno", None) == 1644:
                        cur.execute("ROLLBACK TO sp_band")
                        continue
                    cur.execute("ROLLBACK TO sp_band")
                    raise
        if booked:
            continue

        # solo booking: try up to 100 artists
        for _ in range(100):
            aid = random.choice(artist_ids)
            if not ok_seq(appearances[aid], yr):
                continue
            cur.execute("SAVEPOINT sp_solo")
            if safe_insert_artist(pid, aid, yr):
                break
            else:
                cur.execute("ROLLBACK TO sp_solo")

# ───────────────────────── 7. ATTENDEES • TICKETS • REVIEWS
print("→ attendees, tickets, reviews")
for t in ("Review", "Ticket", "Attendee"):
    reset_table(t)

# fetch all ticket‑type ids and locate VIP
cur.execute("SELECT type_id, name FROM Ticket_Type")
type_rows = cur.fetchall()
vip_type  = next(r["type_id"] for r in type_rows if r["name"].lower() == "vip")
other_ids = [r["type_id"] for r in type_rows if r["type_id"] != vip_type]

# create attendees
attendees = []
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
    """Return a fresh EAN‑13 complying number each call."""
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

    # up to 80 new buyers (excl. first two special attendees)
    pool = [a for a in attendees[2:] if a not in bought]
    buyers = random.sample(pool, min(80, len(pool)))

    cap       = CAPACITY
    vip_cap   = math.ceil(CAPACITY * 0.10)
    gen_share = len(other_ids)               # equal probability among non‑VIP types

    for idx, aid in enumerate(buyers):
        # 10 % VIP cap, otherwise distribute evenly among remaining ticket types
        if idx < vip_cap:
            t_id = vip_type
        else:
            t_id = other_ids[(idx - vip_cap) % gen_share]

        # choose appropriate status
        if fy > TODAY.year:                         # future festival year
            status = status_id["active"] if random.random() < 0.85 else status_id["on offer"]
        else:                                       # current/past year
            future_ev = is_future
            status = (
                status_id["active"] if future_ev
                else (status_id["used"] if random.random() < 0.80 else status_id["unused"])
            )

        try:
            cur.execute(
                """INSERT INTO Ticket
                        (type_id, purchase_date, cost, method_id, ean_number,
                            status_id, attendee_id, event_id)
                    VALUES (%s,      %s,            %s,   %s,        %s,
                            %s,       %s,           %s)""",
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
            # ignore duplicate or capacity‑triggered skips
            if getattr(e, "errno", None) not in (1062, 45000):
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
        
# ───────────────────────── 9. RESALE QUEUES FOR FUTURE FESTIVALS ─────────────────────────
print("→ resale queues for future festivals")

# list of future events
future_events = [ev for (yr, _), ev in event_of_day.items() if yr > TODAY.year]

# every ticket_type id
cur.execute("SELECT type_id FROM Ticket_Type")
all_types = [r["type_id"] for r in cur.fetchall()]

ACTIVE = status_id["active"]

for ev in future_events:
    # --- Pull ACTIVE tickets for this event
    cur.execute("""
        SELECT ticket_id, attendee_id, type_id
        FROM Ticket
        WHERE event_id = %s AND status_id = %s
    """, (ev, ACTIVE))
    tickets = cur.fetchall()
    random.shuffle(tickets)

    if not tickets:
        continue

    # --- 9.a  First‑wave OFFERS  (up‑to‑10, never >½ of active tickets)
    max_pairs = min(10, len(tickets) // 2)
    offers1   = tickets[:max_pairs]                    # first batch
    for row in offers1:
        cur.execute(
            "INSERT INTO Resale_Offer (ticket_id, event_id, seller_id)"
            " VALUES (%s, %s, %s)",
            (row["ticket_id"], ev, row["attendee_id"])
        )
    offered_types = {r["type_id"] for r in offers1}

    # --- 9.b  INTERESTS (exactly max_pairs rows) – ½ match now, ½ later
    # buyers without ticket for this event
    cur.execute("SELECT attendee_id FROM Ticket WHERE event_id=%s", (ev,))
    holders = {r["attendee_id"] for r in cur.fetchall()}
    pool = [a for a in attendees if a not in holders]
    buyers = random.sample(pool, max_pairs)

    half = max_pairs // 2
    for i, buyer in enumerate(buyers):
        # even idx → request a currently offered type (guaranteed immediate match)
        if i < half:
            typ = random.choice(list(offered_types))
        # odd idx → request a type *not* offered yet (forces later offer‑trigger match)
        else:
            not_offered = [t for t in all_types if t not in offered_types]
            typ = random.choice(not_offered or all_types)

        cur.execute(
            "INSERT INTO Resale_Interest (buyer_id, event_id) VALUES (%s,%s)",
            (buyer, ev)
        )
        req = cur.lastrowid
        cur.execute(
            "INSERT INTO Resale_Interest_Type (request_id, type_id) VALUES (%s,%s)",
            (req, typ)
        )

    # at this point:
    # • half the interests matched existing offers ⇒ ↓offer rows + ↓interest rows
    # • the other half remain as pending interests

    # --- 9.c  Second‑wave OFFERS – one per *pending* interest (guaranteed offer match)
    cur.execute("""
        SELECT rit.type_id
        FROM Resale_Interest ri
        JOIN Resale_Interest_Type rit USING (request_id)
        WHERE ri.event_id = %s
    """, (ev,))
    pending_types = [r["type_id"] for r in cur.fetchall()]

    for typ in pending_types:
        # find an unused ACTIVE ticket of that type
        cur.execute("""
            SELECT ticket_id, attendee_id
            FROM Ticket
            WHERE event_id = %s
                AND type_id  = %s
                AND status_id = %s
                AND NOT EXISTS (
                    SELECT 1 FROM Resale_Offer ro
                    WHERE ro.ticket_id = Ticket.ticket_id)
            LIMIT 1
        """, (ev, typ, ACTIVE))
        row = cur.fetchone()
        if not row:           # rare: no suitable ticket left – skip
            continue

        cur.execute(
            "INSERT INTO Resale_Offer (ticket_id, event_id, seller_id)"
            " VALUES (%s, %s, %s)",
            (row["ticket_id"], ev, row["attendee_id"])
        )

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
        ["python3", "../../cli/db137.py", "db-status"],
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

    Path("../../docs/organization/db_data.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("[OK] db_data.txt written.")

except subprocess.CalledProcessError as e:
    print("[ERROR] Failed to run db137 db-status:")
    print(e.stderr or e)
