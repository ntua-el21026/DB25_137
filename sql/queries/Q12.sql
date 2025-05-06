-- SQL query for Q12
-- We assume that the working day an event takes place
-- is the calendar date in which it starts

SELECT
    DATE(e.start_dt) AS event_day,
    'security' AS staff_role,
    SUM(CEIL(s.capacity * 0.05)) AS required_staff
FROM Event e
JOIN Stage s ON e.stage_id = s.stage_id
GROUP BY event_day

UNION ALL

SELECT
    DATE(e.start_dt) AS event_day,
    'support' AS staff_role,
    SUM(CEIL(s.capacity * 0.02)) AS required_staff
FROM Event e
JOIN Stage s ON e.stage_id = s.stage_id
GROUP BY event_day

ORDER BY event_day, staff_role;

-- Index used:
-- idx_event_start on Event(start_dt)
