-- SQL query for Q3
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    v.fest_year,
    COUNT(*) AS warm_up_count
FROM View_Performance_Detail v
JOIN Artist a ON a.artist_id = v.artist_id
WHERE v.perf_type = 'warm up'
GROUP BY a.artist_id, artist_name, v.fest_year
HAVING COUNT(*) > 2
ORDER BY warm_up_count DESC;
