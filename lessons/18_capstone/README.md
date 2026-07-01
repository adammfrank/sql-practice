# Lesson 18 — Capstone: a slow multi-table report

This is the final exam. No new concept — just everything you've learned,
applied to one deliberately slow report.

## The report

> **The top 10 products by revenue from paid orders in the last 7 days,
> with each product's total review count.**

"Last 7 days" is anchored to a **fixed date**, not `now()`: the seeded data
is a fixed snapshot whose most recent order is dated 2023-11-14, so the
window is `created_at >= '2023-11-07'`. (Using `now()` would match zero
rows — the data doesn't reach the present day.)

The correct result is defined by [`expected.sql`](expected.sql). Your
[`solution.sql`](solution.sql) must return **exactly the same 10 rows in
the same order**.

## Why the naive query is slow

`expected.sql` is written the obvious way, and with no helpful indexes it:

- **Seq-Scans `orders`** (500K rows) to find the paid, recent ones,
- **Seq-Scans `order_items`** (1M rows) to join and sum revenue,
- **Seq-Scans `reviews`** (1M rows) to count reviews per product.

Three full scans of large tables to produce ten rows.

Note one thing the naive query gets *right*: it computes revenue and review
counts in **two separate aggregations** (two CTEs) before joining. If you
instead join `order_items` and `reviews` to `products` in one flat query,
the two one-to-many relationships multiply and **inflate revenue by the
review count** — a classic fan-out bug. Keep the aggregations separate.

## Your job

1. In [`indexes.sql`](indexes.sql), create the indexes that let the planner
   reach each large table through an index instead of a Seq Scan.
2. In [`solution.sql`](solution.sql), write the query. You may keep the
   naive shape or rewrite it — as long as the rows match. A good rewrite
   ranks the top 10 products by revenue **first**, then looks up review
   counts for just those 10 (so you never count all 1M reviews).

Techniques in play — most of the course:

- **Composite index** on the order filter (`status`, `created_at`) so the
  recent paid orders are found without scanning all 500K.
- **Indexing a foreign-key column** (`order_items.order_id`) — FKs aren't
  indexed automatically. A **covering `INCLUDE`** of `product_id, quantity,
  price` can make the item lookup an **index-only scan**.
- **Indexing `reviews.product_id`** so the review counts are index lookups.
- **`ORDER BY ... LIMIT`** to return only the top 10.
- **Avoiding the fan-out** described above.

## Run it

```bash
.venv/Scripts/pytest lessons/18_capstone -v
```

## The gate

1. **Correctness** — same 10 rows, same order, as `expected.sql`.
2. **Plan** — **no `Seq Scan` on `orders`, `order_items`, or `reviews`.**
   This is the primary gate. (A Seq Scan on the tiny `products` table is
   fine — for 10K rows it's often the optimal hash-join build side.)
3. **Speed** — at least **6× faster** than the naive baseline.

## A note on the target

Earlier lessons chased 8–10× speedups by making a query touch *few* rows.
This report is different: it must aggregate every order_item in the window
(~11K of them) no matter how clever you are, so there's a floor on how fast
it can go. The win here comes from not touching the rows you *don't* need —
skipping the other ~989K order_items, the other ~490K orders, and all 1M
reviews except the handful for your top products. Measured end to end,
that's about a **10× improvement**; the gate asks for 6× to stay reliable
across machines. Some reports are inherently scan-bound — recognizing which
part of a query has a floor, and shrinking everything around it, is itself
the lesson.
