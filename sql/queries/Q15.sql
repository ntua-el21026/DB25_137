-- SQL query for Q15
SELECT
    att.attendee_id,
    CONCAT(att.first_name, ' ', att.last_name) AS attendee_name,
    CONCAT(ar.first_name, ' ', ar.last_name)   AS artist_name,
    SUM(r.overall) AS total_score
FROM Review r
JOIN Performance_Artist pa ON r.perf_id = pa.perf_id
JOIN Artist ar ON pa.artist_id = ar.artist_id
JOIN Attendee att ON r.attendee_id = att.attendee_id
GROUP BY att.attendee_id, artist_name
ORDER BY total_score DESC
LIMIT 5;
