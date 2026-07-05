# Lesson 07 — Statistics, Selectivity, and `ANALYZE`

Every lesson so far has been about giving the planner an index to use.
This one is different: there's no index to add, and getting it right
isn't really about editing a file — it's a **hands-on lab**. You'll
clone the database, skew it the way a real production surge would, and
watch the query planner make a bad estimate from stale statistics, then
fix it and watch the estimate snap back into line.

The planner has to *guess*, before it runs anything, how many rows a
predicate will match — that guess is how it chooses between a sequential
scan, an index scan, a nested loop, and so on. The guesses come from
**statistics**: a compact per-column summary stored in `pg_statistic`
(readable via the friendlier `pg_stats` view) and refreshed by
`ANALYZE`. When the statistics go stale, the guesses go wrong, and the
planner picks bad plans even when a perfect index exists.

## 1. The problem

Picture a "day-2 order surge": a burst of new `'pending'` orders lands
in `orders`, and nobody has run `ANALYZE` yet (autovacuum will get to
it, but not for a while). Postgres still believes `'pending'` is about
1-in-6 of the table — the ratio it measured at the last `ANALYZE`,
before the surge — so its estimate for how many rows match
`status = 'pending'` is now far too low.

## 2. Explore it yourself

This lesson ships a `setup.sql` that inserts 200,000 new `'pending'`
orders (ids above the current max, and crucially **no** `ANALYZE`
afterward). Spin up a lab database with that already applied:

```bash
make lab lessons/07_statistics
```

That clones the seeded template into `dojo_lab_07_statistics`, runs the
insert, and drops you into a `psql` session connected to it. Now walk
the scenario by hand:

1. **See the stale estimate.** Run a plain `EXPLAIN` — *not* `EXPLAIN
   ANALYZE` — on a query selecting `id` from `orders` where `status` is
   `'pending'`. Read the `rows=` figure in the top line: that's the
   planner's guess.
2. **See the truth.** Run a `count(*)` of that same filter. It's far
   higher than the guess — those are the 200,000 rows the planner
   doesn't know about yet.
3. **Fix it.** Run `ANALYZE` on the `orders` table.
4. **Watch the estimate correct itself.** Run the same `EXPLAIN` again;
   `rows=` now lands within a percent or two of the real count.

On the seeded data you'll see roughly a **stale estimate of ~115,000**,
a **real count of ~284,000**, and — after `ANALYZE` — a **fresh
estimate of ~286,000**. Note the plan stays a `Seq Scan` throughout
(there's no index on `status`): the point isn't the plan *shape*, it's
how wrong the planner's *numbers* were until you refreshed the stats.

Use `EXPLAIN` (the estimate), not `EXPLAIN ANALYZE` — the latter runs
the query and reports the *real* row count, which hides the very gap
you're trying to see.

When you're done, drop the lab database (running `make lab` again also
re-creates it fresh, so you can always start over):

```bash
make lab-clean
```

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

You can inspect all of this directly by selecting `attname`,
`n_distinct`, `most_common_vals`, and `most_common_freqs` from the
`pg_stats` view, filtered to `tablename = 'orders'` and
`attname = 'status'` — try it in the lab, before and after `ANALYZE`.

### Correlated columns: `CREATE STATISTICS`

Ordinary per-column statistics assume columns are independent. If
`status` and `customer_id` are correlated in some way the planner
doesn't know about (e.g. certain customers are disproportionately
`'cancelled'`), a query filtering on both together can still get a bad
estimate even with fresh single-column stats, because Postgres
multiplies the two columns' individual selectivities as if they were
unrelated. Extended statistics tell it not to assume that: you'd create
a `CREATE STATISTICS` object of the `dependencies` kind over `status`
and `customer_id` on `orders`, then run `ANALYZE` on the table so the
new statistics get populated.

`CREATE STATISTICS` is worth knowing about any time you see a
multi-column filter whose estimated row count looks suspicious even
after a plain `ANALYZE`.

## 5. Optional: confirm it the way the other lessons do

If you'd rather have an automated check, `solution.sql` is still a stub.
Put the same `ANALYZE` statement in it and run:

```bash
make test lessons/07_statistics
```

The gate applies the *same* `setup.sql`, records the planner's estimate,
runs your `solution.sql`, and asserts the estimate is now within 25% of
the true count. It's the one lesson whose gate compares planner
*estimates* rather than query results or plan shape — which is exactly
why it never fit the "add an index, beat the baseline" mold, and why the
lab above is the better way to feel what's going on.

## 6. The teaching point

An index can only help if the planner's cost model correctly predicts
that using it is cheap — and that prediction is only as good as the
statistics behind it. `ANALYZE` is cheap, safe, and something you
should reach for immediately whenever a query's `EXPLAIN` (not
`EXPLAIN ANALYZE`) row estimate looks implausible relative to reality,
especially after bulk loads, large deletes, or backfills. Autovacuum
runs `ANALYZE` automatically too, but only after enough rows have
changed (`autovacuum_analyze_scale_factor`) — for one-off bulk changes,
running it explicitly afterward is a habit worth having.
