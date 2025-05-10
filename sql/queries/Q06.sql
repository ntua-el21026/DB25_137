-- SQL query for Q6
SELECT event_id, event_title, avg_event_rating
FROM View_Attendee_Event_Rating
WHERE attendee_id = 69;

-- Analysis od the simple plan
EXPLAIN
SELECT event_id, event_title, avg_event_rating
FROM View_Attendee_Event_Rating
WHERE attendee_id = 69;

EXPLAIN ANALYZE
SELECT event_id, event_title, avg_event_rating
FROM View_Attendee_Event_Rating
WHERE attendee_id = 69;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;

-- Alternative query plan with force index
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
WHERE t.attendee_id = 69
GROUP BY e.event_id, e.title;

-- Explain of the alternative plan
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
WHERE t.attendee_id = 69
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
WHERE t.attendee_id = 69
GROUP BY e.event_id, e.title;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;
