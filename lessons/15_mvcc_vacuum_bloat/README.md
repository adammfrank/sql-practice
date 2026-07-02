# Lesson 15 — MVCC, Dead Tuples, and `VACUUM`

Every lesson so far has been about the query planner: giving it an
index, fresh statistics, or a plan shape it can exploit. This lesson
is about something underneath all of that — how Postgres actually
stores row versions on disk, and what happens when you `UPDATE` or
`DELETE` a lot of rows.

## 1. MVCC in one paragraph

Postgres uses **MVCC** (Multi-Version Concurrency Control): it never
overwrites a row in place. An `UPDATE` doesn't modify the existing row
version — it inserts a brand-new row version (with a new transaction
ID visibility range) and marks the old version as obsolete. A
`DELETE` just marks the row's version as obsolete; it doesn't reclaim
the space. This is what lets readers and writers avoid blocking each
other: an old snapshot can keep seeing the old row version while a
writer is busy creating a new one.

The obsolete versions left behind are called **dead tuples**. They
still occupy space in the table's heap until something reclaims them.

## 2. The problem

This lesson's test simulates a common operational event: a bulk
`UPDATE` touches half a million rows in `events` — it appends a small
key onto each row's `payload` JSONB for every `id <= 500000`.

Every one of those 500,000 rows now has two versions on disk: the old
(dead) one and the new (live) one. Nothing has reclaimed the dead
versions yet. You can see this directly by selecting `n_live_tup` and
`n_dead_tup` from `pg_stat_user_tables` for `relname = 'events'`.

`n_dead_tup` will read roughly 500,000. Those dead tuples aren't free:
they bloat the table's on-disk size (`pg_relation_size('events')`
grows), they make sequential scans read more pages than the live data
alone would need, and they slow down index lookups that have to
consult the visibility information for stale row versions.

## 3. Autovacuum — and why it isn't the answer here

In a real, long-running database, **autovacuum** is a background
process that wakes up periodically and reclaims dead tuples
automatically, once enough of a table has changed
(`autovacuum_vacuum_scale_factor` / `autovacuum_vacuum_threshold`).
Most of the time you never think about this — it Just Works.

This lesson's test setup deliberately disables autovacuum on the
`events` table first, via an `ALTER TABLE` that sets the table's
`autovacuum_enabled` storage parameter to false.

Why? So the measurement is deterministic. If autovacuum were left on,
it might (or might not) fire mid-test and clean up the dead tuples for
you, on its own schedule — making the "before" and "after" numbers
non-reproducible. In production you'd rarely disable autovacuum like
this; here it's purely to make the lesson's before/after comparison
reliable.

## 4. What to do

In `solution.sql`, reclaim the dead tuples by running `VACUUM` on the
`events` table.

`VACUUM` scans the table, identifies dead tuples that no active
transaction could still need to see, and marks their space as
reusable. (Plain `VACUUM`, without `FULL`, doesn't shrink the file on
disk — it just makes the space available for future inserts/updates
within the existing file — but it does immediately update
`n_dead_tup` back down.)

**Important:** `VACUUM` cannot run inside a transaction block (you'll
get `ERROR: VACUUM cannot run inside a transaction block` if you try
`BEGIN; VACUUM events; COMMIT;`). If you're running this by hand in
`psql`, just run it directly — psql isn't in a transaction unless you
started one.

## 5. `fillfactor` and HOT updates

Two related concepts worth knowing, even though the gate doesn't
require them here:

- **`fillfactor`**: a per-table storage parameter (default 100, i.e.
  fully packed) that tells Postgres to leave some free space in each
  page when writing rows — e.g. setting the table's `fillfactor` to 90
  reserves 10% free space per page. That reserved space gives
  **HOT updates** (Heap-Only Tuples) somewhere to put the new row
  version *on the same page* as the old one, when the update doesn't
  touch any indexed columns. HOT updates are cheaper: they don't
  require inserting new entries into every index on the table, only
  into the heap.
- Lowering `fillfactor` trades a bit of wasted space (and thus a
  slightly larger table) for cheaper updates on tables that get
  updated frequently — a classic operational tuning knob for
  update-heavy tables.

## 6. Run it

```bash
.venv/Scripts/pytest lessons/15_mvcc_vacuum_bloat -v
```

## 7. The gate

This lesson's gate is dead-tuple-based, not row-correctness-based
(`expected.sql` is a harmless placeholder — see its comment). The
test:

1. Disables autovacuum on `events` for this clone, so it can't
   interfere with the measurement.
2. Runs the bulk `UPDATE` above and commits it.
3. Reads `n_dead_tup` from `pg_stat_user_tables` — clearing the stats
   snapshot first (`pg_stat_clear_snapshot()`) since the stats
   collector can otherwise report stale numbers, and polling in a
   bounded loop (up to ~3s) in case of a brief lag. Asserts this
   "before" count is above 400,000, as a hard self-check that the
   scenario is actually set up (if it isn't, that's a test bug, not
   yours).
4. Runs your `solution.sql` on a separate autocommit connection to the
   same database (since `VACUUM` can't run in a transaction block).
5. Re-reads `n_dead_tup` (clearing the snapshot again) and asserts it
   dropped by at least 90% from the "before" count.

With the placeholder `SELECT 1;` still in `solution.sql`, nothing gets
vacuumed, so the "after" count stays roughly equal to "before" — the
gate fails clearly. Only an actual `VACUUM events;` (or `VACUUM
events, ...` covering it, or `VACUUM;` the whole database) drives the
count down far enough to pass.

## 8. The teaching point

Dead tuples aren't a bug — they're the necessary cost of MVCC's
lock-free reads. But left unchecked (autovacuum disabled, or unable to
keep up with a very high update/delete rate), they bloat tables and
indexes, slow down scans, and — in the worst case, if `n_dead_tup`
grows enormous and transaction IDs wrap — can force emergency
`VACUUM FREEZE` situations. Knowing how to read `pg_stat_user_tables`
and reach for a manual `VACUUM` after a large bulk `UPDATE`/`DELETE`
(rather than waiting on autovacuum's schedule) is a core operational
skill, distinct from anything the query planner can fix for you.
