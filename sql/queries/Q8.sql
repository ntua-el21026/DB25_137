-- SQL query for Q8
SELECT
    st.staff_id,
    CONCAT(st.first_name, ' ', st.last_name) AS staff_name
FROM Staff st
JOIN Staff_Role sr ON st.role_id = sr.role_id
WHERE sr.name = 'support'
  AND NOT EXISTS (
    SELECT 1
    FROM Works_On wo
    JOIN Event e ON wo.event_id = e.event_id
    JOIN Performance p ON e.event_id = p.event_id
    WHERE wo.staff_id = st.staff_id
      AND DATE(p.datetime) = '2025-06-18'  -- replace with target date
);
