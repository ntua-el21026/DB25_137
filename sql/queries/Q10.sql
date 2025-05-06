-- SQL query for Q10
-- We assume that we are interested in artitsts
-- that actually have perrformed (in a past date)

SELECT
    gp.genre_id1,
    g1.name AS genre_name_1,
    gp.genre_id2,
    g2.name AS genre_name_2,
    gp.artist_count
FROM View_Genre_Pairs gp
JOIN Genre g1 ON gp.genre_id1 = g1.genre_id
JOIN Genre g2 ON gp.genre_id2 = g2.genre_id
ORDER BY gp.artist_count DESC
LIMIT 3;

-- Indexes used:
-- idx_artist_genre_by_artist on Artist_Genre(artist_id, genre_id)
-- idx_artist_genre on Artist_Genre(genre_id, artist_id)
-- idx_perf_artist on Performance_Artist(artist_id, perf_id)
-- idx_perf_event_type on Performance(event_id, type_id)
-- idx_event_year on Event(fest_year)

-- View used:
-- View_Genre_Pairs
