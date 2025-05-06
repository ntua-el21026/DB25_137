-- SQL query for Q1

SELECT
    yr.fest_year,
    pm.name AS payment_method,
    yr.total_revenue
FROM View_Yearly_Revenue_By_Method yr
JOIN Payment_Method pm ON yr.method_id = pm.method_id
ORDER BY yr.fest_year, pm.name;

-- Indexes used:
-- idx_ticket_event_date_payment, on Ticket(event_id, purchase_date, method_id)
-- idx_event_year, on Event(fest_year)

-- View used:
-- View_Yearly_Revenue_By_Method
