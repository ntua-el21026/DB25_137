----------------
--- Indexing ---
----------------

USE pulse_university;

/* -----------------------------------------------------------
 * 1.  Ticket-centric queries   (Q 1, 6, 9, 15)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_ticket_event_date_payment ON Ticket;
DROP INDEX IF EXISTS idx_ticket_attendee_event     ON Ticket;

CREATE INDEX idx_ticket_event_date_payment ON Ticket (event_id, purchase_date, method_id);
CREATE INDEX idx_ticket_attendee_event     ON Ticket (attendee_id, event_id);

/* -----------------------------------------------------------
 * 2.  Event / festival helpers   (Q 1, 7, 12, 14)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_event_year ON Event;

CREATE INDEX idx_event_year ON Event (fest_year);          -- yearly roll-ups

/* -----------------------------------------------------------
 * 3.  Genres & sub-genres   (Q 2, 10)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_artist_genre           ON Artist_Genre;
DROP INDEX IF EXISTS idx_artist_genre_by_artist ON Artist_Genre;
DROP INDEX IF EXISTS idx_artist_subgenre        ON Artist_SubGenre;

CREATE INDEX idx_artist_genre           ON Artist_Genre (genre_id, artist_id);   -- filter-first
CREATE INDEX idx_artist_genre_by_artist ON Artist_Genre (artist_id, genre_id);   -- self-join path
CREATE INDEX idx_artist_subgenre        ON Artist_SubGenre (sub_genre_id, artist_id);

DROP INDEX IF EXISTS idx_band_genre     ON Band_Genre;
DROP INDEX IF EXISTS idx_band_subgenre  ON Band_SubGenre;

CREATE INDEX idx_band_genre    ON Band_Genre  (genre_id, band_id);
CREATE INDEX idx_band_subgenre ON Band_SubGenre (sub_genre_id, band_id);

/* ------ speeds Genre → SubGenre cascades -------- */
DROP INDEX IF EXISTS idx_subgenre_genre ON SubGenre;
CREATE INDEX idx_subgenre_genre         ON SubGenre (genre_id);

/* -----------------------------------------------------------
 * 4.  Artist attributes   (Q 5, 13)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_artist_dob ON Artist;
CREATE INDEX idx_artist_dob         ON Artist (date_of_birth);     -- “young artists” filter

/* -----------------------------------------------------------
 * 5.  Performance look-ups   (Q 3, 4, 10, 11, 14)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_perf_event_type ON Performance;
DROP INDEX IF EXISTS idx_perf_type       ON Performance;
DROP INDEX IF EXISTS idx_perf_datetime   ON Performance;

CREATE INDEX idx_perf_event_type ON Performance (event_id, type_id);
CREATE INDEX idx_perf_type       ON Performance (type_id);        -- quick “warm-up” filter
CREATE INDEX idx_perf_datetime   ON Performance (datetime);

DROP INDEX IF EXISTS idx_perf_artist ON Performance_Artist;
DROP INDEX IF EXISTS idx_perf_band   ON Performance_Band;

CREATE INDEX idx_perf_artist ON Performance_Artist (artist_id, perf_id);
CREATE INDEX idx_perf_band   ON Performance_Band   (band_id,  perf_id);

/* -----------------------------------------------------------
 * 6.  Staff & staffing ratios   (Q 7, 8, 12)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_workson_event_staff ON Works_On;
DROP INDEX IF EXISTS idx_staff_role_staff    ON Staff;
DROP INDEX IF EXISTS idx_staff_experience    ON Staff;

CREATE INDEX idx_workson_event_staff ON Works_On (event_id, staff_id);   -- event-centric scans
CREATE INDEX idx_staff_role_staff    ON Staff    (role_id,  staff_id);   -- role filter + join
CREATE INDEX idx_staff_experience    ON Staff    (experience_id);

/* -----------------------------------------------------------
 * 7.  Reviews   (Q 4, 6, 15)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_review_perf_io          ON Review;
DROP INDEX IF EXISTS idx_review_attendee_overall ON Review;

CREATE INDEX idx_review_perf_io          -- covering index
        ON Review (perf_id, interpretation, overall);
CREATE INDEX idx_review_attendee_overall
        ON Review (attendee_id, overall);

/* -----------------------------------------------------------
 * 8.  Geography   (Q 13)
 * -----------------------------------------------------------*/
DROP INDEX IF EXISTS idx_location_continent ON Location;
CREATE INDEX idx_location_continent         ON Location (continent_id);
