----------------
----- Views ----
----------------

USE pulse_university;

/* ============  drop old versions if they exist  ============ */
DROP VIEW IF EXISTS View_Artist_Performance;
DROP VIEW IF EXISTS View_Event_Staff;
DROP VIEW IF EXISTS View_Attendee_Performance;
DROP VIEW IF EXISTS View_Genre_Pairs;
DROP VIEW IF EXISTS View_Artist_Continents;
DROP VIEW IF EXISTS View_Performance_Detail;
DROP VIEW IF EXISTS View_Genre_Year_Counts;
DROP VIEW IF EXISTS View_Attendee_Yearly_Visits;

/* ------------------------------------------------------------
 * View 1 – artist workload & average ratings (Q 4, 11)
 * ------------------------------------------------------------*/
CREATE VIEW View_Artist_Performance AS
SELECT  a.artist_id,
        CONCAT(a.first_name,' ',a.last_name) AS artist_name,
        COUNT(pa.perf_id)                    AS performance_count,
        AVG(r.interpretation)                AS avg_interpretation,
        AVG(r.overall)                       AS avg_overall
FROM    Artist a
LEFT JOIN Performance_Artist pa ON a.artist_id = pa.artist_id
LEFT JOIN Review             r  ON pa.perf_id  = r.perf_id
GROUP BY a.artist_id, artist_name;

/* ------------------------------------------------------------
 * View 2 – event staffing vs required ratios (Q 7, 12)
 * ------------------------------------------------------------*/
CREATE VIEW View_Event_Staff AS
SELECT e.event_id, e.title, s.capacity,
        /* actual security & support numbers */
        SUM(CASE WHEN st.role_id = (SELECT role_id FROM Staff_Role WHERE name='security' LIMIT 1)
                	THEN 1 ELSE 0 END) AS security_count,
        SUM(CASE WHEN st.role_id = (SELECT role_id FROM Staff_Role WHERE name='support'  LIMIT 1)
                	THEN 1 ELSE 0 END) AS support_count,
        /* required head-counts */
        CEIL(s.capacity*0.05) AS required_security,
        CEIL(s.capacity*0.02) AS required_support
FROM    Event e
JOIN    Works_On wo ON e.event_id  = wo.event_id
JOIN    Staff    st ON wo.staff_id = st.staff_id
JOIN    Stage    s  ON e.stage_id  = s.stage_id
GROUP BY e.event_id, e.title, s.capacity;

/* ------------------------------------------------------------
 * View 3 – attendee’s watched performances & own rating (Q 6)
 * ------------------------------------------------------------*/
CREATE VIEW View_Attendee_Performance AS
SELECT  att.attendee_id,
        CONCAT(att.first_name,' ',att.last_name) AS attendee_name,
        p.perf_id,
        e.title AS event_title,
        AVG(r.overall) AS attendee_avg_rating   -- NULL until they review
FROM    Ticket     t
JOIN      Event       e   ON t.event_id      = e.event_id
JOIN      Performance p   ON p.event_id      = e.event_id
JOIN      Attendee    att ON att.attendee_id = t.attendee_id
LEFT JOIN Review      r   ON r.perf_id       = p.perf_id
                          AND r.attendee_id  = att.attendee_id
GROUP BY att.attendee_id, attendee_name, p.perf_id, e.title;

/* ------------------------------------------------------------
 * View 4 – unique artist-genre pairs & artist count (Q 10)
            only for artist that actually have performed
 * ------------------------------------------------------------*/
CREATE VIEW View_Genre_Pairs AS
SELECT
    LEAST(ag1.genre_id, ag2.genre_id)    AS genre_id1,
    GREATEST(ag1.genre_id, ag2.genre_id) AS genre_id2,
    COUNT(DISTINCT ag1.artist_id)        AS artist_count
FROM Artist_Genre ag1
JOIN Artist_Genre ag2
  ON ag1.artist_id = ag2.artist_id AND ag1.genre_id < ag2.genre_id
WHERE ag1.artist_id IN (
    SELECT DISTINCT pa.artist_id
    FROM Performance_Artist pa
    JOIN Performance p ON pa.perf_id  = p.perf_id
    JOIN Event       e ON p.event_id  = e.event_id
    JOIN Festival    f ON e.fest_year = f.fest_year
    WHERE f.fest_year < YEAR(CURDATE())
)
GROUP BY genre_id1, genre_id2;


/* ------------------------------------------------------------
 * View 5 – artists & number of continents performed in (Q 13)
 * ------------------------------------------------------------*/
CREATE VIEW View_Artist_Continents AS
SELECT  a.artist_id,
        CONCAT(a.first_name,' ',a.last_name) AS artist_name,
        COUNT(DISTINCT l.continent_id)       AS continents_performed
FROM    Artist a
JOIN    Performance_Artist pa ON a.artist_id = pa.artist_id
JOIN    Performance        p  ON pa.perf_id  = p.perf_id
JOIN    Event              e  ON p.event_id  = e.event_id
JOIN    Festival           f  ON e.fest_year = f.fest_year
JOIN    Location           l  ON f.loc_id    = l.loc_id
GROUP BY a.artist_id, artist_name;

/* ------------------------------------------------------------
 * View 6 – handy performance detail (Q 2, 3, 5, 11 & others)
 *          one row per performer–performance, with fest year & type
 * ------------------------------------------------------------*/
CREATE VIEW View_Performance_Detail AS
SELECT p.perf_id,
       p.event_id,
       e.fest_year,
       pt.name AS perf_type,
       p.datetime,
       pa.artist_id,
       pb.band_id
FROM Performance p
JOIN      Event              e  ON p.event_id = e.event_id
JOIN      Performance_Type   pt ON p.type_id  = pt.type_id
LEFT JOIN Performance_Artist pa ON pa.perf_id = p.perf_id
LEFT JOIN Performance_Band   pb ON pb.perf_id = p.perf_id;

/* ------------------------------------------------------------
 * View 7 – yearly appearances per genre (Q 14)
 * ------------------------------------------------------------*/
CREATE VIEW View_Genre_Year_Counts AS
SELECT  g.genre_id,
        g.name   AS genre_name,
        d.fest_year,
        COUNT(*) AS perf_count
FROM    View_Performance_Detail d
JOIN    Artist_Genre ag ON ag.artist_id = d.artist_id
JOIN    Genre        g  ON g.genre_id   = ag.genre_id
GROUP BY g.genre_id, g.name, d.fest_year;

/* ------------------------------------------------------------
 * View 8 – attendee visit count per calendar year (Q 9)
 * ------------------------------------------------------------*/
CREATE VIEW View_Attendee_Yearly_Visits AS
SELECT  t.attendee_id,
        YEAR(t.purchase_date)      AS festival_year,
        COUNT(DISTINCT t.event_id) AS events_attended
FROM    Ticket t
GROUP BY t.attendee_id, YEAR(t.purchase_date);

/* ------------------------------------------------------------
 * View 9 – aggregates per attendee–artist pair (Q 15)
 * ------------------------------------------------------------*/
CREATE VIEW View_Attendee_Artist_Review AS
SELECT
    r.attendee_id,
    pa.artist_id,
    SUM(r.overall) AS total_score
FROM Review r
JOIN Performance_Artist pa ON r.perf_id = pa.perf_id
GROUP BY r.attendee_id, pa.artist_id;
