# Lesson 07 — Statistics, Selectivity, and `ANALYZE`

Every lesson so far has been about giving the planner an index to use.
This lesson is about something more fundamental: the planner has to
*guess*, in advance, how many rows a predicate will match, before it
can decide whether an index is even worth using. Those guesses come
from **statistics** — a compact summary of each column's data,
stored in `pg_statistic` (readable via the friendlier `pg_stats`
view) and refreshed by `ANALYZE`. If the statistics are stale, the
planner's guesses can be badly wrong, and it will pick a bad plan even
when a perfectly good index exists.

## 1. The problem

This lesson's test simulates something that happens constantly in a
live system: a burst of new rows lands in `orders` — say, a flood of
newly created `'pending'` orders — and nobody has run `ANALYZE` yet.
Autovacuum will get to it eventually, but "eventually" might be
minutes away, and in the meantime the planner is working from
out-of-date statistics.

Before you touch anything, the test:

1. Inserts 200,000 new rows into `orders`, all with
   `status = 'pending'`, using IDs above the existing max — a
   realistic "day 2 order surge" — **without** running `ANALYZE`
   afterward.
2. Runs `EXPLAIN` (no `ANALYZE`, just the planner's estimate) on:

   ```sql
   SELECT id FROM orders WHERE status = 'pending';
   ```

   Postgres still believes the table has roughly the row counts and
   value frequencies it saw at the *last* `ANALYZE` — from before the
   200,000 new `'pending'` rows existed. So its estimate for how many
   rows match `status = 'pending'` is now far too low: it doesn't know
   `'pending'` just became far more common than it used to be.

Try it yourself first:

```sql
EXPLAIN SELECT id FROM orders WHERE status = 'pending';
```

Compare the `rows=` estimate in the plan to the real count:

```sql
SELECT count(*) FROM orders WHERE status = 'pending';
```

They will disagree substantially.

## 2. What to do

In `solution.sql`, tell Postgres to recompute statistics for the
table that changed:

```sql
ANALYZE orders;
```

That's it — `ANALYZE` samples the table's rows and rebuilds the
per-column statistics (most common values and their frequencies,
a histogram of the rest, `n_distinct`, null fraction, and so on) that
the query planner's cost estimator relies on for every plan it builds
touching that table.

## 3. Why this matters even when you're "just adding an index"

A bad row-count estimate doesn't just cost you a fraction of a
percent of accuracy — it can flip the planner's decision entirely.
The planner chooses between a sequential scan, an index scan, a
nested loop, a hash join, and so on, based on which it *estimates*
will be cheapest. If it thinks a predicate matches 1,000 rows when it
actually matches 280,000, it may:

- Skip an index that would have been an easy win, because it (wrongly)
  believes a sequential scan is competitive.
- Pick a Nested Loop join expecting a small number of outer rows, and
  end up probing the inner side hundreds of thousands of times.
- Underestimate memory needed for a hash table and spill to disk.

Every lesson before this one implicitly assumed fresh statistics. In
production, statistics go stale constantly: bulk loads, backfills,
status columns whose value distribution shifts over time (like this
lesson's `'pending'` surge), and any table that changes faster than
autovacuum's analyze threshold keeps up with.

## 4. `pg_statistic`, `n_distinct`, and histograms

`ANALYZE` doesn't scan the whole table — it takes a random sample
(size controlled by each column's `STATISTICS TARGET`, default 100)
and estimates, for each column:

- **Most Common Values (MCVs)** and their frequencies — e.g. Postgres
  might record that `'paid'` accounts for ~50% of `status` values.
- **A histogram** of the remaining, less-common values, used to
  estimate range and inequality predicates (`>`, `<`, `BETWEEN`).
- **`n_distinct`** — an estimate of how many distinct values the
  column has, used when there's no exact MCV match.
- **Null fraction**, average width, and correlation with physical row
  order (this last one matters for deciding whether an index scan
  will be mostly-sequential or mostly-random I/O).

You can inspect all of this directly:

```sql
SELECT attname, n_distinct, most_common_vals, most_common_freqs
FROM pg_stats
WHERE tablename = 'orders' AND attname = 'status';
```

### Correlated columns: `CREATE STATISTICS`

Ordinary per-column statistics assume columns are independent. If
`status` and `customer_id` are correlated in some way the planner
doesn't know about (e.g. certain customers are disproportionately
`'cancelled'`), a query filtering on both together can still get a bad
estimate even with fresh single-column stats, because Postgres
multiplies the two columns' individual selectivities as if they were
unrelated. Extended statistics tell it not to assume that:

```sql
CREATE STATISTICS orders_status_customer_stats (dependencies)
ON status, customer_id FROM orders;
ANALYZE orders;
```

This lesson's gate only requires the `ANALYZE`, but `CREATE STATISTICS`
is worth knowing about any time you see a multi-column filter whose
estimated row count looks suspicious even after a plain `ANALYZE`.

## 5. Run it

```bash
.venv/Scripts/pytest lessons/07_statistics -v
```

## 6. The gate

This lesson's gate is different from every other lesson's — there's
no baseline speed comparison, because the point isn't "make this
query faster," it's "make the planner's estimate *accurate*." The
test:

1. Skews the data (200,000 new `'pending'` rows, no `ANALYZE`).
2. Captures the planner's **estimated** row count for
   `WHERE status = 'pending'` via `EXPLAIN` (no `ANALYZE` keyword —
   this only asks the planner to *estimate*, not actually run the
   query) — this must be badly wrong (more than 25% off the true
   count) before your fix, or the gate isn't testing anything real.
3. Runs your `solution.sql`.
4. Re-captures the estimate the same way, and asserts
   `abs(estimated - actual) / actual < 0.25` — the estimate must now
   be within 25% of the true row count.

## 7. The teaching point

An index can only help if the planner's cost model correctly predicts
that using it is cheap — and that prediction is only as good as the
statistics behind it. `ANALYZE` is cheap, safe, and something you
should reach for immediately whenever a query's `EXPLAIN` (not
`EXPLAIN ANALYZE`) row estimate looks implausible relative to reality,
especially after bulk loads, large deletes, or backfills. Autovacuum
runs `ANALYZE` automatically too, but only after enough rows have
changed (`autovacuum_analyze_scale_factor`) — for one-off bulk changes,
running it explicitly afterward is a habit worth having.
