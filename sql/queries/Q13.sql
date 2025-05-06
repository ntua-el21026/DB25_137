-- SQL query for Q13

SELECT
    ac.artist_id,
    ac.artist_name,
    ac.continents_performed
FROM View_Artist_Continents ac
WHERE ac.continents_performed >= 3
ORDER BY ac.continents_performed DESC, ac.artist_name;

-- Indexes used (via the View):
-- idx_perf_artist on Performance_Artist(artist_id, perf_id)
-- idx_event_year on Event(fest_year)
-- idx_location_continent on Location(continent_id)

-- View used:
-- View_Artist_Continents
