-- SQL query for Q12
-- We assume that the working day an event takes place
-- is the calendar date in which it starts

SELECT
    DATE(e.start_dt) AS event_day,
    sr.name AS staff_role,
    SUM(
        CASE
            WHEN sr.name = 'security' THEN CEIL(s.capacity * 0.05)
            WHEN sr.name = 'support'  THEN CEIL(s.capacity * 0.02)
        END
    ) AS required_staff
FROM Event e
JOIN Stage      s  ON e.stage_id  = s.stage_id
JOIN Staff_Role sr ON sr.name IN ('security', 'support')    -- idx_staff_role_name
JOIN Festival   f  ON e.fest_year = f.fest_year             -- idx_event_year
WHERE f.fest_year = 2025  -- or any other valid festival year
GROUP BY event_day, sr.name
ORDER BY event_day, sr.name;

-- Indexes used
-- idx_event_start: Event(start_dt)
-- idx_staff_role_name: Staff_Role(name)
-- idx_event_year: Event(fest_year)
