-- SQL query for Q1

SELECT
    f.fest_year,
    pm.name AS payment_method,
    SUM(t.cost) AS total_revenue
FROM Ticket t
JOIN Event e ON t.event_id = e.event_id             -- idx_ticket_event_date_payment
JOIN Festival f ON e.fest_year = f.fest_year        -- idx_event_year
JOIN Payment_Method pm ON t.method_id = pm.method_id
GROUP BY f.fest_year, pm.name
ORDER BY f.fest_year, pm.name;

-- Indexes used
-- idx_ticket_event_date_payment: Ticket(event_id, purchase_date, method_id)
-- idx_event_year: Event(fest_year)
