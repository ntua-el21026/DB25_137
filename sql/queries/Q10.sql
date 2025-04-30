-- SQL query for Q10
WITH Performing_Artists AS (
    SELECT DISTINCT artist_id
    FROM Performance_Artist
),
Genre_Pairs AS (
    SELECT
        LEAST(ag1.genre_id, ag2.genre_id) AS genre_id1,
        GREATEST(ag1.genre_id, ag2.genre_id) AS genre_id2,
        ag1.artist_id
    FROM Artist_Genre ag1
    JOIN Artist_Genre ag2
        ON ag1.artist_id = ag2.artist_id AND ag1.genre_id < ag2.genre_id
    WHERE ag1.artist_id IN (SELECT artist_id FROM Performing_Artists)
)
SELECT
    gp.genre_id1,
    g1.name AS genre_name_1,
    gp.genre_id2,
    g2.name AS genre_name_2,
    COUNT(DISTINCT gp.artist_id) AS artist_count
FROM Genre_Pairs gp
JOIN Genre g1 ON gp.genre_id1 = g1.genre_id
JOIN Genre g2 ON gp.genre_id2 = g2.genre_id
GROUP BY gp.genre_id1, gp.genre_id2, g1.name, g2.name
ORDER BY artist_count DESC
LIMIT 3;

