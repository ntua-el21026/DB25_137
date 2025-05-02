-- SQL query for Q11

WITH Artist_Performance_Count AS (
    SELECT
        a.artist_id,
        CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
        COUNT(pa.perf_id) AS performance_count
    FROM Artist a
    JOIN Performance_Artist pa ON a.artist_id = pa.artist_id    -- idx_perf_artist
    GROUP BY a.artist_id, artist_name
),
Max_Performer AS (
    SELECT MAX(performance_count) AS max_perf
    FROM Artist_Performance_Count
)
SELECT
    ap.artist_id,
    ap.artist_name,
    ap.performance_count
FROM Artist_Performance_Count ap
JOIN Max_Performer mp ON ap.performance_count <= mp.max_perf - 5
ORDER BY ap.performance_count DESC;

-- Index used
-- idx_perf_artist: Performance_Artist(artist_id, perf_id)
