-- SQL query for Q4
SELECT artist_id, artist_name, avg_interpretation, avg_overall
FROM View_Artist_Performance_Rating
WHERE artist_id = 42;

-- Analysis of the simple query
EXPLAIN
SELECT artist_id, artist_name, avg_interpretation, avg_overall
FROM View_Artist_Performance_Rating
WHERE artist_id = 42;

EXPLAIN ANALYZE
SELECT artist_id, artist_name, avg_interpretation, avg_overall
FROM View_Artist_Performance_Rating
WHERE artist_id = 42;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;

-- Alternative Query Plan with force index
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Artist a
JOIN Performance_Artist pa FORCE INDEX (idx_perf_artist) ON a.artist_id = pa.artist_id
JOIN Review r FORCE INDEX (idx_review_perf_io) ON pa.perf_id = r.perf_id
WHERE a.artist_id = 42
GROUP BY a.artist_id, artist_name;

-- Analysis of the alternate plan
EXPLAIN
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Artist a
JOIN Performance_Artist pa FORCE INDEX (idx_perf_artist) ON a.artist_id = pa.artist_id
JOIN Review r FORCE INDEX (idx_review_perf_io) ON pa.perf_id = r.perf_id
WHERE a.artist_id = 42
GROUP BY a.artist_id, artist_name;

EXPLAIN ANALYZE
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Artist a
JOIN Performance_Artist pa FORCE INDEX (idx_perf_artist) ON a.artist_id = pa.artist_id
JOIN Review r FORCE INDEX (idx_review_perf_io) ON pa.perf_id = r.perf_id
WHERE a.artist_id = 42
GROUP BY a.artist_id, artist_name;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;
