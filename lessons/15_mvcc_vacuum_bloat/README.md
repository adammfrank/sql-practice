# Lesson 15 — MVCC, Dead Tuples, and `VACUUM`

Every lesson so far has been about the query planner. This one is about
what's underneath: how Postgres stores row versions, and what a big
`UPDATE`/`DELETE` leaves behind.

## 1. MVCC and dead tuples

Postgres uses **MVCC** (Multi-Version Concurrency Control): it never
overwrites a row in place. An `UPDATE` inserts a new row version and
marks the old one obsolete; a `DELETE` just marks it obsolete. This lets
readers and writers avoid blocking each other — an old snapshot keeps
seeing the old version. Those obsolete versions are **dead tuples**, and
they occupy heap space until something reclaims them.

## 2. The problem

The test simulates a common event: a bulk `UPDATE` appends a key to the
`payload` of every `events` row with `id <= 500000`. Each of those
500,000 rows now has a dead old version plus a live new one. You can see
this via `n_dead_tup` in `pg_stat_user_tables` for `relname = 'events'`
— it reads ~500,000. Dead tuples bloat the table, make seq scans read
more pages, and slow index lookups that must check stale versions'
visibility.

(The test disables autovacuum on the clone first, only so the
before/after measurement is deterministic — in production, autovacuum
normally reclaims dead tuples on its own.)

## 3. What to do

In `solution.sql`, reclaim the dead tuples by running **`VACUUM` on the
`events` table**.

Plain `VACUUM` marks dead-tuple space reusable and drops `n_dead_tup`
immediately (it doesn't shrink the file on disk — that needs
`VACUUM FULL`). **`VACUUM` cannot run inside a transaction block**, so
don't wrap it in `BEGIN; ... COMMIT;`.

## 4. `fillfactor` and HOT updates (context, not gated)

`fillfactor` (default 100) reserves free space per page; lowering it
(e.g. to 90) gives **HOT updates** room to put a new row version on the
same page as the old one when no indexed column changed — avoiding new
index entries. It trades a little space for cheaper updates on
update-heavy tables.

## 5. Run it

```bash
make test lessons/15_mvcc_vacuum_bloat
```

## 6. The gate

Dead-tuple-based, not row-correctness (`expected.sql` is a placeholder).
The test disables autovacuum, runs the bulk `UPDATE`, asserts the
"before" `n_dead_tup` is above 400,000, runs your `solution.sql` on a
separate autocommit connection (since `VACUUM` can't run in a
transaction), then asserts `n_dead_tup` dropped by at least 90%. The
placeholder `SELECT 1;` vacuums nothing and fails; `VACUUM events;` (or
`VACUUM;` for the whole database) passes.

## 7. The teaching point

Dead tuples are the necessary cost of MVCC's lock-free reads — but left
unchecked (autovacuum disabled, or unable to keep up with a very high
update/delete rate) they bloat tables and indexes and, in the worst case
(transaction-ID wraparound), force emergency freezes. Reading
`pg_stat_user_tables` and reaching for a manual `VACUUM` after a large
bulk `UPDATE`/`DELETE`, rather than waiting on autovacuum's schedule, is
a core operational skill the planner can't do for you.
