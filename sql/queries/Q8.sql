-- SQL query for Q8
-- We assume that the working day an event takes place
-- is the calendar date in which it starts

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
    WHERE wo.staff_id = st.staff_id
      AND e.start_dt >= '2025-06-18' AND e.start_dt < '2025-06-19' -- or any other date
);

-- Indexes used:
-- idx_staff_role_staff on Staff(role_id)
-- idx_workson_event_staff on Works_On(staff_id, event_id)
-- idx_event_start on Event(start_dt)

-- Comment: We use this weird phrasing in line 16, in order for
-- idx_event_start to work effectively
