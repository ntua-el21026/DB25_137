-- SQL query for Q2

SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    g.name AS genre_name,
    CASE
        WHEN ap.artist_id IS NOT NULL THEN 'Yes'
        ELSE 'No'
    END AS participated
FROM Artist a
JOIN Artist_Genre ag ON a.artist_id = ag.artist_id
JOIN Genre        g  ON ag.genre_id = g.genre_id
LEFT JOIN View_Artist_Year_Participation ap
    ON ap.artist_id = a.artist_id AND ap.fest_year = YEAR(CURDATE())
WHERE g.name = 'Rock' -- or any other genre

-- Indexes used:
-- idx_perf_artist on Performance_Artist(artist_id, perf_id)
-- idx_event_year on Event(fest_year)
-- idx_artist_genre_by_artist on Artist_Genre(artist_id, genre_id)
-- idx_perf_event_type on Performance(event_id, type_id)

-- View used:
-- View_Artist_Year_Participation
