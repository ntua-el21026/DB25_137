-- SQL query for Q9
WITH Yearly_Visit_Counts AS (
    SELECT
        t.attendee_id,
        YEAR(t.purchase_date) AS year,
        COUNT(DISTINCT t.event_id) AS event_count
    FROM Ticket t
    GROUP BY t.attendee_id, YEAR(t.purchase_date)
    HAVING COUNT(DISTINCT t.event_id) > 3
),
Matching_Visits AS (
    SELECT year, event_count
    FROM Yearly_Visit_Counts
    GROUP BY year, event_count
    HAVING COUNT(*) > 1
)
SELECT
    yvc.attendee_id,
    CONCAT(a.first_name, ' ', a.last_name) AS attendee_name,
    yvc.year,
    yvc.event_count
FROM Yearly_Visit_Counts yvc
JOIN Matching_Visits mv ON yvc.year = mv.year AND yvc.event_count = mv.event_count
JOIN Attendee a ON a.attendee_id = yvc.attendee_id
ORDER BY yvc.year, yvc.event_count DESC;
