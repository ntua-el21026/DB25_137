-- SQL query for Q8
-- We assume that the working day an event takes place
-- is the calendar date in which it starts

SELECT
  st.staff_id,
  CONCAT(st.first_name, ' ', st.last_name) AS staff_name
FROM Staff st
JOIN Staff_Role sr ON st.role_id = sr.role_id -- idx_staff_role_staff
WHERE sr.name = 'support'
  AND NOT EXISTS (
    SELECT 1
    FROM Works_On wo
    JOIN Event e ON wo.event_id = e.event_id  -- idx_workson_event_staff, idx_event_start
    WHERE wo.staff_id = st.staff_id
      AND DATE(e.start_dt) = '2025-06-18'  -- or any other date
);

-- Indexes used
-- idx_staff_role_staff: Staff(role_id)
-- idx_workson_event_staff: Works_On(staff_id, event_id)
-- idx_event_start: Event(start_dt)
