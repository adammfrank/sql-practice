# Answer notes — 13

1. A composite index `(asset_id, status)`. Column order matters here:
   `asset_id` first because it's the more selective/equality predicate
   the query always filters on, `status` second so the index can satisfy
   both conditions in one lookup rather than filtering `status` after the
   fact. `(status, asset_id)` would work too for *this exact query* since
   both are equality predicates, but `(asset_id, status)` is the safer
   general default — it also serves a lookup that filters on `asset_id`
   alone, whereas `(status, ...)` alone is nearly useless (low
   cardinality, filters out only ~10% of rows).
2. No — low selectivity is the red flag. An index on `severity` alone
   would only be worth it if `critical` rows are a small fraction of the
   table (matches the "90% low/medium" framing — `critical` is presumably
   rare). Before adding it, check `EXPLAIN` on the actual query and the
   real value distribution (`GROUP BY severity, COUNT(*)`) — if the
   planner already prefers a seq scan for a *common* value like `medium`,
   that's correct behavior, not a missing index.
3. Only skip deciding which rows to read (an Index Scan / Bitmap Scan to
   find matching rows, then a heap fetch for the rest of each row) —
   unless the index also covers `asset_id` (e.g. `CREATE INDEX ...
   (status) INCLUDE (asset_id)`, or a composite `(status, asset_id)`),
   in which case Postgres can answer the whole `GROUP BY` from the index
   alone (Index Only Scan) without touching the heap at all.
4. `EXPLAIN (ANALYZE, BUFFERS)` on the actual query — see the real plan
   and real timings before guessing at an index or rewrite.
