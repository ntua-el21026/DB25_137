-- SQL query for Q10

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
