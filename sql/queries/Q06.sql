-- PLAN 1 ----------------------------------------------------------------
-- The simple method
SELECT event_id, event_title, avg_event_rating
FROM View_Attendee_Event_Rating
WHERE attendee_id = 42;

EXPLAIN
SELECT event_id, event_title, avg_event_rating
FROM View_Attendee_Event_Rating
WHERE attendee_id = 42;

EXPLAIN ANALYZE
SELECT event_id, event_title, avg_event_rating
FROM View_Attendee_Event_Rating
WHERE attendee_id = 42;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;

-- PLAN 2 ----------------------------------------------------------------
-- Alternative method with force indexing
SELECT
    e.event_id,
    e.title AS event_title,
    AVG(r.overall) AS avg_event_rating
FROM Ticket t FORCE INDEX (idx_ticket_attendee_event)
JOIN Event       e   ON t.event_id      = e.event_id
JOIN Attendee    att ON att.attendee_id = t.attendee_id
JOIN Performance p   ON p.event_id      = e.event_id
LEFT JOIN Review r FORCE INDEX (idx_review_attendee_overall) 
                     ON r.perf_id       = p.perf_id
                    AND r.attendee_id   = att.attendee_id
WHERE t.attendee_id = 42
GROUP BY e.event_id, e.title;

EXPLAIN
SELECT
    e.event_id,
    e.title AS event_title,
    AVG(r.overall) AS avg_event_rating
FROM Ticket t FORCE INDEX (idx_ticket_attendee_event)
JOIN Event       e   ON t.event_id      = e.event_id
JOIN Attendee    att ON att.attendee_id = t.attendee_id
JOIN Performance p   ON p.event_id      = e.event_id
LEFT JOIN Review r FORCE INDEX (idx_review_attendee_overall) 
                     ON r.perf_id       = p.perf_id
                    AND r.attendee_id   = att.attendee_id
WHERE t.attendee_id = 42
GROUP BY e.event_id, e.title;

EXPLAIN ANALYZE
SELECT
    e.event_id,
    e.title AS event_title,
    AVG(r.overall) AS avg_event_rating
FROM Ticket t FORCE INDEX (idx_ticket_attendee_event)
JOIN Event       e   ON t.event_id      = e.event_id
JOIN Attendee    att ON att.attendee_id = t.attendee_id
JOIN Performance p   ON p.event_id      = e.event_id
LEFT JOIN Review r FORCE INDEX (idx_review_attendee_overall) 
                     ON r.perf_id       = p.perf_id
                    AND r.attendee_id   = att.attendee_id
WHERE t.attendee_id = 42
GROUP BY e.event_id, e.title;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;

-- PLAN 3 ----------------------------------------------------------------
-- Comparisson of hash vs nested loop join, without indexes

-- Hash join option - Allow hashing, forbid BKA
SET @saved_switch := @@optimizer_switch;
SET optimizer_switch = 'batched_key_access=off,block_nested_loop=on';

SELECT /*+ BNL(r) NO_BKA(r) */
    e.event_id,
    e.title        AS event_title,
    AVG(r.overall) AS avg_event_rating
FROM Review r USE INDEX ()
STRAIGHT_JOIN Performance p   USE INDEX () ON p.perf_id       = r.perf_id
STRAIGHT_JOIN Ticket      t   USE INDEX () ON t.event_id      = p.event_id
                                          AND t.attendee_id   = r.attendee_id
STRAIGHT_JOIN Event       e   USE INDEX () ON e.event_id      = t.event_id
STRAIGHT_JOIN Attendee    att USE INDEX () ON att.attendee_id = t.attendee_id
WHERE t.attendee_id = 42
GROUP BY e.event_id, e.title;

EXPLAIN
SELECT /*+ BNL(r) NO_BKA(r) */
    e.event_id,
    e.title        AS event_title,
    AVG(r.overall) AS avg_event_rating
FROM Review r USE INDEX ()
STRAIGHT_JOIN Performance p   USE INDEX () ON p.perf_id       = r.perf_id
STRAIGHT_JOIN Ticket      t   USE INDEX () ON t.event_id      = p.event_id
                                          AND t.attendee_id   = r.attendee_id
STRAIGHT_JOIN Event       e   USE INDEX () ON e.event_id      = t.event_id
STRAIGHT_JOIN Attendee    att USE INDEX () ON att.attendee_id = t.attendee_id
WHERE t.attendee_id = 42
GROUP BY e.event_id, e.title;

EXPLAIN ANALYZE
SELECT /*+ BNL(r) NO_BKA(r) */
    e.event_id,
    e.title        AS event_title,
    AVG(r.overall) AS avg_event_rating
FROM Review r USE INDEX ()
STRAIGHT_JOIN Performance p   USE INDEX () ON p.perf_id       = r.perf_id
STRAIGHT_JOIN Ticket      t   USE INDEX () ON t.event_id      = p.event_id
                                          AND t.attendee_id   = r.attendee_id
STRAIGHT_JOIN Event       e   USE INDEX () ON e.event_id      = t.event_id
STRAIGHT_JOIN Attendee    att USE INDEX () ON att.attendee_id = t.attendee_id
WHERE t.attendee_id = 42
GROUP BY e.event_id, e.title;

SET optimizer_switch = @saved_switch;

-- Nested loop join option - Forbid hashing, allow BKA
SET @saved_switch := @@optimizer_switch;
SET optimizer_switch = 'batched_key_access=on,block_nested_loop=off';

EXPLAIN ANALYZE
SELECT /*+ NO_BNL(r) BKA(r) */
    e.event_id,
    e.title        AS event_title,
    AVG(r.overall) AS avg_event_rating
FROM Review r USE INDEX ()
STRAIGHT_JOIN Performance p   USE INDEX () ON p.perf_id       = r.perf_id
STRAIGHT_JOIN Ticket      t   USE INDEX () ON t.event_id      = p.event_id
                                          AND t.attendee_id   = r.attendee_id
STRAIGHT_JOIN Event       e   USE INDEX () ON e.event_id      = t.event_id
STRAIGHT_JOIN Attendee    att USE INDEX () ON att.attendee_id = t.attendee_id
WHERE t.attendee_id = 42
GROUP BY e.event_id, e.title;

SET optimizer_switch = @saved_switch;