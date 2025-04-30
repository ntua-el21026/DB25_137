-- SQL query for Q2
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    g.name AS genre_name,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM Performance_Artist pa
            JOIN Performance p ON pa.perf_id = p.perf_id
            JOIN Event e ON p.event_id = e.event_id
            WHERE pa.artist_id = a.artist_id
        )
        THEN 'Yes'
        ELSE 'No'
    END AS participated
FROM Artist a
JOIN Artist_Genre ag ON a.artist_id = ag.artist_id
JOIN Genre g ON ag.genre_id = g.genre_id
WHERE g.name = 'Rock'  -- or any other genre
ORDER BY artist_name;
