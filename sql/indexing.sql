----------------
--- Indexing ---
----------------

USE pulse_university;

/* -----------------------------------------------------------
 * 1.  Ticket-centric queries   (Q 1, 8, 9)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_ticket_event_date_payment  ON Ticket;
DROP INDEX IF EXISTS idx_ticket_attendee_event      ON Ticket;
DROP INDEX IF EXISTS idx_ticket_attendee_year_event ON Ticket;

CREATE INDEX idx_ticket_event_date_payment  ON Ticket (event_id, purchase_date, method_id);
CREATE INDEX idx_ticket_attendee_event      ON Ticket (attendee_id, event_id);
CREATE INDEX idx_ticket_attendee_year_event ON Ticket (attendee_id, purchase_date, event_id);

/* -----------------------------------------------------------
 * 2.  Event / festival helpers   (Q 1, 2, 3, 7, 8, 10, 13, 14)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_event_year  ON Event;
DROP INDEX IF EXISTS idx_event_start ON Event;

CREATE INDEX idx_event_year  ON Event (fest_year);      -- yearly roll-ups
CREATE INDEX idx_event_start ON Event(start_dt);

/* -----------------------------------------------------------
 * 3.  Genres & sub-genres   (Q 2, 10, 14)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_artist_genre           ON Artist_Genre;
DROP INDEX IF EXISTS idx_artist_genre_by_artist ON Artist_Genre;

CREATE INDEX idx_artist_genre           ON Artist_Genre (genre_id, artist_id);   -- filter-first
CREATE INDEX idx_artist_genre_by_artist ON Artist_Genre (artist_id, genre_id);   -- self-join path

/* -----------------------------------------------------------
 * 4.  Artist attributes   (Q 5)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_artist_dob ON Artist;
CREATE INDEX idx_artist_dob         ON Artist (date_of_birth);  -- “young artists” filter

/* -----------------------------------------------------------
 * 5.  Performance look-ups   (Q 2, 3, 5, 10, 11, 13, 14, 15)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_perf_event_type ON Performance;
DROP INDEX IF EXISTS idx_perf_type       ON Performance;
DROP INDEX IF EXISTS idx_perf_datetime   ON Performance;
DROP INDEX IF EXISTS idx_perf_artist ON Performance_Artist;

CREATE INDEX idx_perf_event_type ON Performance (event_id, type_id);
CREATE INDEX idx_perf_type       ON Performance (type_id);        -- quick “warm-up” filter
CREATE INDEX idx_perf_datetime   ON Performance (datetime);
CREATE INDEX idx_perf_artist ON Performance_Artist (artist_id, perf_id);

/* -----------------------------------------------------------
 * 6.  Staff & staffing ratios   (Q 7, 8)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_workson_event_staff ON Works_On;
DROP INDEX IF EXISTS idx_staff_role_staff    ON Staff;
DROP INDEX IF EXISTS idx_staff_experience    ON Staff;

CREATE INDEX idx_workson_event_staff ON Works_On (event_id, staff_id);   -- event-centric scans
CREATE INDEX idx_staff_role_staff    ON Staff    (role_id,  staff_id);   -- role filter + join
CREATE INDEX idx_staff_experience    ON Staff    (experience_id);

/* -----------------------------------------------------------
 * 7.  Reviews   (Q 11, 15)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_review_perf_io          ON Review;
DROP INDEX IF EXISTS idx_review_attendee_overall ON Review;

CREATE INDEX idx_review_perf_io          ON Review (perf_id, interpretation, overall); -- covering index
CREATE INDEX idx_review_attendee_overall ON Review (attendee_id, overall); -- possibly for 4, 6

/* -----------------------------------------------------------
 * 8.  Geography   (Q 13)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_location_continent ON Location;

CREATE INDEX idx_location_continent         ON Location (continent_id);
