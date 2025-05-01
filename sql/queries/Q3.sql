-- SQL query for Q3

SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    v.fest_year,
    COUNT(*) AS warm_up_count
FROM View_Performance_Detail v
JOIN Artist a ON a.artist_id = v.artist_id      -- idx_perf_artist
WHERE v.perf_type = 'warm up'                   -- idx_perf_type
GROUP BY a.artist_id, artist_name, v.fest_year
HAVING COUNT(*) > 2
ORDER BY warm_up_count DESC;

-- Indexes used
-- idx_perf_type: Performance(type_id)
-- idx_perf_artist: Performance_Artist(artist_id, perf_id)
-- idx_event_year: Event(fest_year) inside View_Performance_Detail
