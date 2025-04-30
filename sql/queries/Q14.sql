-- SQL query for Q14
WITH GenreCounts AS (
    SELECT
        genre_id,
        genre_name,
        fest_year,
        perf_count
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
    JOIN GenreCounts gc2 ON gc1.genre_id = gc2.genre_id
                        AND gc2.fest_year = gc1.fest_year + 1
                        AND gc1.perf_count = gc2.perf_count
)
SELECT
    genre_id,
    genre_name,
    year1,
    year2,
    perf_count
FROM ConsecutiveMatch
ORDER BY genre_name, year1;
