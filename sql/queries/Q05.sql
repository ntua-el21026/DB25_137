-- SQL query for Q5

WITH YoungArtists AS (
    SELECT
        a.artist_id,
        CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
        TIMESTAMPDIFF(YEAR, a.date_of_birth, CURDATE()) AS age
    FROM Artist a
    WHERE TIMESTAMPDIFF(YEAR, a.date_of_birth, CURDATE()) < 30
),
MaxPerf AS (
    SELECT MAX(v.performance_count) AS max_perf
    FROM View_Artist_Performance_Rating v
    JOIN YoungArtists ya ON v.artist_id = ya.artist_id
)
SELECT
    ya.artist_id,
    ya.artist_name,
    ya.age,
    v.performance_count
FROM View_Artist_Performance_Rating v
JOIN YoungArtists ya ON v.artist_id = ya.artist_id
JOIN MaxPerf mp ON v.performance_count = mp.max_perf;

-- Indexes used
-- idx_perf_artist: Performance_Artist(artist_id, perf_id)
-- idx_artist_dob: Artist(date_of_birth)
