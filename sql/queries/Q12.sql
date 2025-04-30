-- SQL query for Q12
SELECT
    f.fest_year,
    DATE(p.datetime) AS perf_date,
    e.event_id,
    e.title AS event_title,
    s.capacity,
    
    -- Required staff
    CEIL(s.capacity * 0.05) AS required_security,
    CEIL(s.capacity * 0.02) AS required_support,

    -- Actual staff counts
    SUM(CASE WHEN sr.name = 'security' THEN 1 ELSE 0 END) AS security_count,
    SUM(CASE WHEN sr.name = 'support'  THEN 1 ELSE 0 END) AS support_count

FROM Event e
JOIN Festival f ON e.fest_year = f.fest_year
JOIN Stage s ON e.stage_id = s.stage_id
JOIN Performance p ON p.event_id = e.event_id
JOIN Works_On wo ON wo.event_id = e.event_id
JOIN Staff st ON wo.staff_id = st.staff_id
JOIN Staff_Role sr ON st.role_id = sr.role_id

GROUP BY f.fest_year, perf_date, e.event_id, e.title, s.capacity
ORDER BY f.fest_year, perf_date, e.event_id;
