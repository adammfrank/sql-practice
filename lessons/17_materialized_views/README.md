# Lesson 17 — Materialized Views

Every earlier lesson made a query reach the same fresh answer more
efficiently. This one is different: **precompute the answer once, store
it, and read the stored copy** — at the cost of it going stale until you
refresh.

## 1. The problem

Lesson 01's aggregate — revenue per category for paid orders: join
`order_items` to `orders` (`orders.id = order_items.order_id`) and to
`products` (`products.id = order_items.product_id`), keep only
`orders.status = 'paid'`, and for each `products.category` sum
`quantity * price` as revenue.

This joins and aggregates ~1,000,000 `order_items` every run. No index
fixes that — it's an aggregate over most of the table, not a selective
lookup. A dashboard calling it every few seconds redoes the same work for
an answer that only changes when new orders are paid.

## 2. What to do

- In `indexes.sql`, create a **materialized view** named
  **`mv_cat_revenue`** whose body is the query above
  (`CREATE MATERIALIZED VIEW mv_cat_revenue AS ...`), plus a
  **`CREATE UNIQUE INDEX`** on its `category` column.
- In `solution.sql`, select `category, revenue` from `mv_cat_revenue` —
  reading the precomputed rows, not recomputing the aggregate.

A materialized view stores the *result set* as if it were a table (unlike
a plain `VIEW`, which just re-runs its query text each time), so the
`SELECT` returns almost instantly — reading a handful of rows, touching
none of the base tables.

## 3. Staleness and `REFRESH`

The view is a snapshot; new paid orders don't update it. You refresh with
`REFRESH MATERIALIZED VIEW mv_cat_revenue`. Plain `REFRESH` locks the
view exclusively while it recomputes (readers block).
`REFRESH ... CONCURRENTLY` recomputes into a copy and swaps it in so
readers never block — its one requirement is exactly the **unique index**
you created (it needs it to diff old rows against new), and like `VACUUM`
it can't run inside a transaction block.

## 4. Run it

```bash
make test lessons/17_materialized_views
```

## 5. The gate

Same shape as the ratio-graded lessons, but the "index" is the matview.
`expected.sql` (the live aggregate) is both the answer key and the
baseline, measured **before** `indexes.sql` runs. Then the matview is
created, your `solution.sql` is checked for correctness against
`expected.sql` (same rows, different source), and its execution time must
be at least **20x faster** than the live aggregate. (Reading a few
precomputed rows vs. a million-row join clears that by orders of
magnitude.)

## 6. The teaching point

Materialized views trade freshness for speed: right when a result changes
far less often than it's read and "current as of the last refresh" is
acceptable (a nightly dashboard, an hourly leaderboard), not when it must
reflect the last committed transaction (an account balance). Choosing
"add an index and keep the live query" vs. "materialize the result and
refresh on a schedule" is an operational judgment — which is why this
lesson gates on speed, not plan shape.
