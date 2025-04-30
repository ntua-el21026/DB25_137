-- SQL query for Q7
SELECT
    f.fest_year,
    AVG(el.level_id) AS avg_experience_level
FROM Works_On wo
JOIN Staff st ON wo.staff_id = st.staff_id
JOIN Experience_Level el ON st.experience_id = el.level_id
JOIN Event e ON wo.event_id = e.event_id
JOIN Festival f ON e.fest_year = f.fest_year
WHERE st.role_id NOT IN (
    SELECT role_id FROM Staff_Role WHERE name IN ('security', 'support')
)
GROUP BY f.fest_year
ORDER BY avg_experience_level ASC
LIMIT 1;
