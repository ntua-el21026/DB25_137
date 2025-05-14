-- PLAN 1 ----------------------------------------------------------------
-- The simple method
SELECT artist_id, artist_name, avg_interpretation, avg_overall
FROM View_Artist_Performance_Rating
WHERE artist_id = 7;

EXPLAIN
SELECT artist_id, artist_name, avg_interpretation, avg_overall
FROM View_Artist_Performance_Rating
WHERE artist_id = 7;

EXPLAIN ANALYZE
SELECT artist_id, artist_name, avg_interpretation, avg_overall
FROM View_Artist_Performance_Rating
WHERE artist_id = 7;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;

-- PLAN 2 ----------------------------------------------------------------
-- Alternative method with force indexing
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Artist a
JOIN Performance_Artist pa FORCE INDEX (idx_perf_artist)    ON a.artist_id = pa.artist_id
JOIN Review             r  FORCE INDEX (idx_review_perf_io) ON pa.perf_id  = r.perf_id
WHERE a.artist_id = 7
GROUP BY a.artist_id, artist_name;

EXPLAIN
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Artist a
JOIN Performance_Artist pa FORCE INDEX (idx_perf_artist)    ON a.artist_id = pa.artist_id
JOIN Review             r  FORCE INDEX (idx_review_perf_io) ON pa.perf_id  = r.perf_id
WHERE a.artist_id = 7
GROUP BY a.artist_id, artist_name;

EXPLAIN ANALYZE
SELECT
    a.artist_id,
    CONCAT(a.first_name, ' ', a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Artist a
JOIN Performance_Artist pa FORCE INDEX (idx_perf_artist)    ON a.artist_id = pa.artist_id
JOIN Review             r  FORCE INDEX (idx_review_perf_io) ON pa.perf_id  = r.perf_id
WHERE a.artist_id = 7
GROUP BY a.artist_id, artist_name;

SELECT TRACE FROM information_schema.optimizer_trace LIMIT 1;

-- PLAN 3 ----------------------------------------------------------------
-- Comparisson of hash vs nested loop join, without indexes

-- Hash join option - Allow hashing, forbid BKA
SET @saved_switch := @@optimizer_switch;
SET optimizer_switch = 'batched_key_access=off,block_nested_loop=on';

SELECT /*+ BNL(r) NO_BKA(r) */
    a.artist_id,
    CONCAT(a.first_name,' ',a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Review r  USE INDEX ()
STRAIGHT_JOIN Performance_Artist pa USE INDEX () ON pa.perf_id  = r.perf_id
STRAIGHT_JOIN Artist             a  USE INDEX () ON a.artist_id = pa.artist_id
WHERE a.artist_id = 7
GROUP BY a.artist_id, artist_name;

EXPLAIN
SELECT /*+ BNL(r) NO_BKA(r) */
    a.artist_id,
    CONCAT(a.first_name,' ',a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Review r  USE INDEX ()
STRAIGHT_JOIN Performance_Artist pa USE INDEX () ON pa.perf_id  = r.perf_id
STRAIGHT_JOIN Artist             a  USE INDEX () ON a.artist_id = pa.artist_id
WHERE a.artist_id = 7
GROUP BY a.artist_id, artist_name;


EXPLAIN ANALYZE
SELECT /*+ BNL(r) NO_BKA(r) */
    a.artist_id,
    CONCAT(a.first_name,' ',a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Review r  USE INDEX ()
STRAIGHT_JOIN Performance_Artist pa USE INDEX () ON pa.perf_id  = r.perf_id
STRAIGHT_JOIN Artist             a  USE INDEX () ON a.artist_id = pa.artist_id
WHERE a.artist_id = 7
GROUP BY a.artist_id, artist_name;

SET optimizer_switch = @saved_switch;

-- Nested loop join option - Forbid hashing, allow BKA
SET @saved_switch := @@optimizer_switch;
SET optimizer_switch = 'batched_key_access=on,block_nested_loop=off';

EXPLAIN ANALYZE
SELECT /*+ NO_BNL(r) BKA(r) */
    a.artist_id,
    CONCAT(a.first_name,' ',a.last_name) AS artist_name,
    AVG(r.interpretation) AS avg_interpretation,
    AVG(r.overall) AS avg_overall
FROM Review r  USE INDEX ()
STRAIGHT_JOIN Performance_Artist pa USE INDEX () ON pa.perf_id  = r.perf_id
STRAIGHT_JOIN Artist             a  USE INDEX () ON a.artist_id = pa.artist_id
WHERE a.artist_id = 7
GROUP BY a.artist_id, artist_name;

SET optimizer_switch = @saved_switch;
