-- --------------
-- - Indexing ---
-- --------------

USE pulse_university;

-- Helper: drop procedure if it exists
-- MYSQL does not support DROP INDEX IF EXISTS!
DROP PROCEDURE IF EXISTS DropIndexIfExists;

CREATE PROCEDURE DropIndexIfExists(tbl VARCHAR(64), idx VARCHAR(64))
    SQL SECURITY INVOKER
    COMMENT 'Drops index only if it exists'
BEGIN
    DECLARE count INT;
    SELECT COUNT(*) INTO count
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
        AND table_name = tbl
        AND index_name = idx;

    IF count > 0 THEN
        SET @stmt = CONCAT('DROP INDEX `', idx, '` ON `', tbl, '`');
        PREPARE s FROM @stmt;
        EXECUTE s;
        DEALLOCATE PREPARE s;
    END IF;
END;

/* -----------------------------------------------------------
 * 1.  Ticket-centric queries   (Q 1, 8, 9)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Ticket', 'idx_ticket_event_date_payment');
CALL DropIndexIfExists('Ticket', 'idx_ticket_attendee_event');
CALL DropIndexIfExists('Ticket', 'idx_ticket_attendee_year_event');

CREATE INDEX idx_ticket_event_date_payment  ON Ticket (event_id, purchase_date, method_id);
CREATE INDEX idx_ticket_attendee_event      ON Ticket (attendee_id, event_id);
CREATE INDEX idx_ticket_attendee_year_event ON Ticket (attendee_id, purchase_date, event_id);

/* -----------------------------------------------------------
 * 2.  Event / festival helpers   (Q 1, 2, 3, 7, 8, 10, 13, 14)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Event', 'idx_event_year');
CALL DropIndexIfExists('Event', 'idx_event_start');

CREATE INDEX idx_event_year  ON Event (fest_year);      -- yearly roll-ups
CREATE INDEX idx_event_start ON Event(start_dt);

/* -----------------------------------------------------------
 * 3.  Genres & sub-genres   (Q 2, 10, 14)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Artist_Genre', 'idx_artist_genre');
CALL DropIndexIfExists('Artist_Genre', 'idx_artist_genre_by_artist');

CREATE INDEX idx_artist_genre           ON Artist_Genre (genre_id, artist_id);   -- filter-first
CREATE INDEX idx_artist_genre_by_artist ON Artist_Genre (artist_id, genre_id);   -- self-join path

/* -----------------------------------------------------------
 * 4.  Artist attributes   (Q 5)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Artist', 'idx_artist_dob');
CREATE INDEX idx_artist_dob ON Artist (date_of_birth);  -- “young artists” filter

/* -----------------------------------------------------------
 * 5.  Performance look-ups   (Q 2, 3, 5, 10, 11, 13, 14, 15)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Performance',        'idx_perf_event_type');
CALL DropIndexIfExists('Performance',        'idx_perf_type');
CALL DropIndexIfExists('Performance',        'idx_perf_datetime');
CALL DropIndexIfExists('Performance_Artist', 'idx_perf_artist');

CREATE INDEX idx_perf_event_type ON Performance (event_id, type_id);
CREATE INDEX idx_perf_type       ON Performance (type_id);        -- quick “warm-up” filter
CREATE INDEX idx_perf_datetime   ON Performance (datetime);
CREATE INDEX idx_perf_artist     ON Performance_Artist (artist_id, perf_id);

/* -----------------------------------------------------------
 * 6.  Staff & staffing ratios   (Q 7, 8)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Works_On', 'idx_workson_event_staff');
CALL DropIndexIfExists('Staff',    'idx_staff_role_staff');
CALL DropIndexIfExists('Staff',    'idx_staff_experience');

CREATE INDEX idx_workson_event_staff ON Works_On (event_id, staff_id);   -- event-centric scans
CREATE INDEX idx_staff_role_staff    ON Staff    (role_id,  staff_id);   -- role filter + join
CREATE INDEX idx_staff_experience    ON Staff    (experience_id);

/* -----------------------------------------------------------
 * 7.  Reviews   (Q 6, 11, 15)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Review', 'idx_review_perf_io');
CALL DropIndexIfExists('Review', 'idx_review_attendee_overall');
CALL DropIndexIfExists('Review', 'idx_review_perf_attendee_overall');

CREATE INDEX idx_review_perf_io               ON Review (perf_id, interpretation, overall); -- covering index
CREATE INDEX idx_review_attendee_overall      ON Review (attendee_id, overall);
CREATE INDEX idx_review_perf_attendee_overall ON Review (perf_id, attendee_id, overall);

/* -----------------------------------------------------------
 * 8.  Geography   (Q 13)
 * -----------------------------------------------------------*/
CALL DropIndexIfExists('Location', 'idx_location_continent');
CREATE INDEX idx_location_continent ON Location (continent_id);

-- Clean up: drop helper procedure
DROP PROCEDURE IF EXISTS DropIndexIfExists;
