-- SQL query for Q5

WITH ArtistCounts AS (
    SELECT
        a.artist_id,
        CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
        TIMESTAMPDIFF(YEAR, a.date_of_birth, CURDATE()) AS age,
        COUNT(pa.perf_id) AS performance_count
    FROM Artist a
    JOIN Performance_Artist pa ON a.artist_id = pa.artist_id    -- idx_perf_artist
    WHERE TIMESTAMPDIFF(YEAR, a.date_of_birth, CURDATE()) < 30  -- idx_artist_dob
    GROUP BY a.artist_id, artist_name
),
MaxCount AS (
    SELECT MAX(performance_count) AS max_perf FROM ArtistCounts
)
SELECT
    ac.artist_id,
    ac.artist_name,
    ac.age,
    ac.performance_count
FROM ArtistCounts ac
JOIN MaxCount mc ON ac.performance_count = mc.max_perf;

-- Indexes used
-- idx_perf_artist: Performance_Artist(artist_id, perf_id)
-- idx_artist_dob: Artist(date_of_birth)
