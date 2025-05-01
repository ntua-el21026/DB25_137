-- SQL query for Q9

WITH FilteredCounts AS (
    SELECT *
    FROM View_Attendee_Yearly_Visits
    WHERE events_attended > 3
),
MatchingCounts AS (
    SELECT festival_year, events_attended
    FROM FilteredCounts
    GROUP BY festival_year, events_attended
    HAVING COUNT(*) > 1
)
SELECT
    fc.attendee_id,
    CONCAT(a.first_name, ' ', a.last_name) AS attendee_name,
    fc.festival_year,
    fc.events_attended
FROM FilteredCounts fc
JOIN MatchingCounts mc ON  fc.festival_year   = mc.festival_year
                       AND fc.events_attended = mc.events_attended
JOIN Attendee       a  ON  fc.attendee_id     = a.attendee_id
ORDER BY fc.festival_year, fc.events_attended DESC;

-- Index used
-- idx_ticket_event_date_payment: Ticket(event_id, purchase_date, method_id)
