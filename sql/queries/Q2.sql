-- SQL query for Q2

SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    g.name AS genre_name,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM Performance_Artist pa
            JOIN Performance p ON pa.perf_id = p.perf_id -- idx_perf_artist
            JOIN Event e ON p.event_id = e.event_id      -- idx_event_year
            WHERE pa.artist_id = a.artist_id
              AND e.fest_year = YEAR(CURDATE())
        )
        THEN 'Yes'
        ELSE 'No'
    END AS participated
FROM Artist a
JOIN Artist_Genre ag ON a.artist_id = ag.artist_id       -- idx_artist_genre_by_artist
JOIN Genre g ON ag.genre_id = g.genre_id
WHERE g.name = 'Jazz' -- or any other genre
ORDER BY artist_name;

-- Indexes used
-- idx_perf_artist: Performance_Artist(artist_id, perf_id)
-- idx_event_year: Event(fest_year)
-- idx_artist_genre_by_artist: Artist_Genre(artist_id, genre_id)
