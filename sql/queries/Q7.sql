-- SQL query for Q7

SELECT
    f.fest_year,
    AVG(el.level_id) AS avg_experience_level
FROM Works_On wo
JOIN Staff            st ON wo.staff_id      = st.staff_id  -- idx_workson_event_staff
JOIN Experience_Level el ON st.experience_id = el.level_id  -- idx_staff_experience
JOIN Event            e  ON wo.event_id      = e.event_id   -- idx_event_year
JOIN Festival         f  ON e.fest_year      = f.fest_year  -- idx_event_year
WHERE st.role_id NOT IN (
    SELECT role_id FROM Staff_Role WHERE name IN ('security', 'support')
)                                                           -- idx_staff_role_staff
GROUP BY f.fest_year
ORDER BY avg_experience_level ASC
LIMIT 1;

-- Indexes used
-- idx_workson_event_staff: Works_On(staff_id, event_id)
-- idx_staff_experience: Staff(experience_id)
-- idx_event_year: Event(fest_year)
-- idx_staff_role_staff: Staff(role_id)
