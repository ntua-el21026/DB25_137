-- SQL query for Q13

SELECT
    ac.artist_id,
    ac.artist_name,
    ac.continents_performed
FROM View_Artist_Continents ac
WHERE ac.continents_performed >= 3
ORDER BY ac.continents_performed DESC, ac.artist_name;
