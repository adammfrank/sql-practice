# Lesson 17 — Materialized Views

Every earlier lesson made a query faster by helping the planner reach
the same fresh answer more efficiently — an index, better statistics,
a partition that gets pruned. This lesson takes a different approach
entirely: **precompute the answer once, store it, and read the stored
copy** — at the cost of that copy going stale until you refresh it.

## 1. The problem

Recall lesson 01's aggregate — total revenue per product category,
for paid orders:

```sql
SELECT p.category, SUM(oi.quantity * oi.price) AS revenue
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'paid'
GROUP BY p.category;
```

This has to join and aggregate across roughly a million `order_items`
rows every single time it runs. No index rescues that fundamentally —
it's an aggregate over most of the table, not a selective lookup. If a
dashboard calls this query every few seconds, you're redoing the same
expensive join and aggregation over and over for an answer that only
changes when new orders are paid.

## 2. Materialized views

A **materialized view** runs a query once and stores its result set
as if it were a real table. You create one with the form
`CREATE MATERIALIZED VIEW <name> AS <query>` — name it `mv_cat_revenue`
and give it the paid-revenue-per-category query from section 1 as its
body.

Once created, `mv_cat_revenue` is queryable exactly like a table —
`SELECT category, revenue FROM mv_cat_revenue;` — and returns
instantly, because it's just reading six already-computed rows off
disk, not touching `order_items`, `orders`, or `products` at all.

This is different from an ordinary (non-materialized) `VIEW`, which is
just a saved query text — querying it still re-runs the underlying
join and aggregation every time. A materialized view actually stores
the *result*.

You can index a materialized view like any table — and here you'll want
a **unique** index on its `category` column (a `CREATE UNIQUE INDEX`).
That isn't just a lookup optimization: it's a prerequisite for one
specific refresh mode, covered next.

## 3. What to do

In `indexes.sql`, create `mv_cat_revenue` (the query above) and a
unique index on `category`. In `solution.sql`, select `category,
revenue` from `mv_cat_revenue` — reading the precomputed rows instead
of recomputing the aggregate.

## 4. Staleness and `REFRESH`

The catch: `mv_cat_revenue` is a snapshot. If new orders get marked
`'paid'` after you create it, the materialized view's rows don't
update on their own — you have to explicitly refresh it:

```sql
REFRESH MATERIALIZED VIEW mv_cat_revenue;
```

Plain `REFRESH` recomputes the whole thing and — importantly — takes
an exclusive lock on the materialized view for the duration, meaning
queries against it block until the refresh finishes. For a view that's
being read constantly, that's often unacceptable.

`REFRESH MATERIALIZED VIEW CONCURRENTLY` avoids that: it recomputes
into a temporary copy and swaps it in, using row-level diffing so
concurrent readers keep seeing the old data (never blocked) until the
new data is ready. Its one requirement is exactly the unique index you
created above — `CONCURRENTLY` needs a unique index on the
materialized view to match old rows to new ones. And like `VACUUM`
(lesson 15), `REFRESH ... CONCURRENTLY` cannot run inside a transaction
block.

## 5. Run it

```bash
.venv/Scripts/pytest lessons/17_materialized_views -v
```

## 6. The gate

This lesson uses the same shape as the ratio-graded indexing lessons,
but the "index" is a materialized view instead:

1. `expected.sql` — the live aggregate (lesson 01's query, verbatim) —
   is both the correctness answer key and the speed baseline.
2. The baseline execution time is measured **before** `indexes.sql`
   runs, so it reflects the real cost of the live join+aggregate over
   ~1,000,000 `order_items` rows, not anything sped up by the
   materialized view.
3. `indexes.sql` creates `mv_cat_revenue` and its unique index.
4. Your `solution.sql` is checked for correctness against
   `expected.sql` (same rows, different source) — the placeholder
   `SELECT 1;` fails this immediately, since `mv_cat_revenue` doesn't
   even exist yet for it to reference, let alone match 6 rows.
5. Your `solution.sql`'s execution time is measured and must be at
   least **20x faster** than the live-aggregate baseline.

Reading 6 precomputed rows is enormously faster than a million-row
join and aggregation — measured in this environment, the live
aggregate took ~186ms and the materialized-view read took ~0.006ms,
comfortably clearing the 20x bar by several orders of magnitude.

## 7. The teaching point

Materialized views trade freshness for speed: they're the right tool
when a query's result changes far less often than it's read, and when
"technically current as of the last refresh" is an acceptable answer
(a nightly sales dashboard, an hourly leaderboard) rather than "must
reflect the last committed transaction" (an account balance). Deciding
between "add an index and keep the live query" versus "materialize the
result and refresh on a schedule" is a real operational judgment call,
not something the planner makes for you — that's why this lesson has
no plan-shape assertion, only a speed comparison against the live
alternative.
