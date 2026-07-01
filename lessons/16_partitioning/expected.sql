-- Canonical correctness answer key: the count for November 2023, computed
-- against the original, unpartitioned `events` table.
SELECT count(*) FROM events WHERE ts >= '2023-11-01' AND ts < '2023-12-01';
