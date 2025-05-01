-- SQL query for Q15

SELECT
    v.attendee_id,
    CONCAT(a.first_name, ' ', a.last_name)   AS attendee_name,
    CONCAT(ar.first_name, ' ', ar.last_name) AS artist_name,
    v.total_score
FROM View_Attendee_Artist_Review v
JOIN Attendee a  ON v.attendee_id = a.attendee_id
JOIN Artist   ar ON v.artist_id   = ar.artist_id
ORDER BY v.total_score DESC
LIMIT 5;
