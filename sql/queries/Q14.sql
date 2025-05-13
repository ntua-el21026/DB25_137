-- SQL query for Q14

WITH GenreCounts AS (
    SELECT *
    FROM View_Genre_Year_Counts
    WHERE perf_count >= 3
),
ConsecutiveMatch AS (
    SELECT
        gc1.genre_id,
        gc1.genre_name,
        gc1.fest_year AS year1,
        gc2.fest_year AS year2,
        gc1.perf_count
    FROM GenreCounts gc1
    JOIN GenreCounts gc2 ON  gc1.genre_id   = gc2.genre_id
                         AND gc2.fest_year  = gc1.fest_year + 1
                         AND gc1.perf_count = gc2.perf_count
)
SELECT
    genre_id,
    genre_name,
    year1,
    year2,
    perf_count
FROM ConsecutiveMatch
ORDER BY genre_name, perf_count, year1;

-- Indexes used (through View_Genre_Year_Counts):
-- idx_perf_type on Performance(type_id)
-- idx_perf_artist on Performance_Artist(artist_id, perf_id)
-- idx_event_year on Event(fest_year)
-- idx_artist_genre on Artist_Genre(genre_id)
-- idx_perf_datetime on Performance(datetime)

-- View used:
-- View_Genre_Year_Counts
