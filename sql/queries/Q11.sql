-- SQL query for Q11

WITH Max_Performer AS (
    SELECT MAX(performance_count) AS max_perf
    FROM View_Artist_Performance_Rating
)
SELECT
    artist_id,
    artist_name,
    performance_count
FROM View_Artist_Performance_Rating
JOIN Max_Performer mp ON performance_count <= mp.max_perf - 5
ORDER BY performance_count DESC;

-- Index used:
-- idx_perf_artist on Performance_Artist(artist_id, perf_id)
-- idx_review_perf_io on Review(perf_id)

-- View used:
-- View_Artist_Performance_Rating
