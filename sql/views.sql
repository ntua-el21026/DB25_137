----------------
----- Views ----
----------------

USE pulse_university;

/* ============  drop old versions if they exist  ============ */
DROP VIEW IF EXISTS View_Attendee_Performance;
DROP VIEW IF EXISTS View_Yearly_Revenue_By_Method;
DROP VIEW IF EXISTS View_Artist_Year_Participation;
DROP VIEW IF EXISTS View_Performance_Detail;
DROP VIEW IF EXISTS View_Attendee_Yearly_Visits;
DROP VIEW IF EXISTS View_Genre_Pairs;
DROP VIEW IF EXISTS View_Artist_Performance;
DROP VIEW IF EXISTS View_Artist_Continents;
DROP VIEW IF EXISTS View_Genre_Year_Counts;
DROP VIEW IF EXISTS View_Attendee_Artist_Review;

/* ------------------------------------------------------------
 * View 0 – attendee’s watched performances & own rating (possibly Q 4, 6)
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
 * View 1 – yearly ticket revenues by payment method (Q 1)
 * ------------------------------------------------------------*/
CREATE VIEW View_Yearly_Revenue_By_Method AS
SELECT
    e.fest_year,
    t.method_id,
    SUM(t.cost) AS total_revenue
FROM Ticket t
JOIN Event e ON t.event_id = e.event_id
GROUP BY e.fest_year, t.method_id;

/* ------------------------------------------------------------
 * View 2 –  artist participation by year (Q 2)
 * ------------------------------------------------------------*/
CREATE VIEW View_Artist_Year_Participation AS
SELECT DISTINCT
    pa.artist_id,
    e.fest_year
FROM Performance_Artist pa
JOIN Performance p ON pa.perf_id = p.perf_id
JOIN Event e ON p.event_id = e.event_id;

/* ------------------------------------------------------------
 * View 3 – handy performance detail (Q 3)
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
 * View 4 – attendee visit count per calendar year (Q 9)
 * ------------------------------------------------------------*/
CREATE VIEW View_Attendee_Yearly_Visits AS
SELECT  t.attendee_id,
        YEAR(t.purchase_date)      AS festival_year,
        COUNT(DISTINCT t.event_id) AS events_attended
FROM    Ticket t
GROUP BY t.attendee_id, YEAR(t.purchase_date);

/* ------------------------------------------------------------
 * View 5 – unique artist-genre pairs & artist count (Q 10)
 *          only for artist that actually have performed
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
 * View 6 – artist workload & average ratings (Q 11)
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
 * View 7 – artists & number of continents performed in (Q 13)
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
 * View 8 – yearly appearances per genre (Q 14)
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
