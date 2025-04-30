-- SQL query for Q5
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    TIMESTAMPDIFF(YEAR, a.date_of_birth, CURDATE()) AS age,
    COUNT(DISTINCT p.event_id) AS festival_appearances
FROM Artist a
JOIN Performance_Artist pa ON a.artist_id = pa.artist_id
JOIN Performance p ON pa.perf_id = p.perf_id
JOIN Event e ON p.event_id = e.event_id
WHERE TIMESTAMPDIFF(YEAR, a.date_of_birth, CURDATE()) < 30
GROUP BY a.artist_id, artist_name
ORDER BY festival_appearances DESC;
