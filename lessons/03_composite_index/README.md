# Lesson 03 — Composite Indexes and Column Order

A single-column index gets you to "all of one customer's orders"
quickly. Real filters are often more specific than that. This lesson
adds a second condition and asks: what index actually helps now?

## 1. The problem

Return the `id`s of `orders` matching both `customer_id = 4242` **and**
`status = 'paid'`.

This is the previous lesson's predicate (`customer_id = 4242`, ~10
rows out of 500,000) narrowed further by `status = 'paid'` (roughly
half of all orders are `'paid'`, the rest split across `pending`,
`shipped`, `cancelled`). Combined, only a handful of rows match.

## 2. What to do

1. In `indexes.sql`, create **one composite index** named
   `idx_orders_cust_status` on `orders`, over both columns in this
   order: `customer_id` first, then `status`.
2. In `solution.sql`, write the query above.

## 3. Why one composite index, not two single-column indexes

You might expect "index `customer_id`, index `status`, let Postgres
combine them" to work just as well. It doesn't, for two reasons:

- **Selectivity is lopsided.** `customer_id = 4242` alone narrows
  500,000 rows down to about 10. `status = 'paid'` alone only narrows
  500,000 down to roughly 250,000 — it's not selective at all by
  itself. An index on `status` alone is nearly useless for this query;
  Postgres would ignore it and lean on `customer_id`, then re-check
  `status` row by row anyway.
- **A composite index does the filtering in one structural step.**
  `(customer_id, status)` is sorted first by `customer_id`, then by
  `status` within each `customer_id`. Postgres seeks straight to the
  `(4242, 'paid')` neighborhood and reads only matching entries — no
  separate index needed for `status`, and no per-row rechecking.

Two single-column indexes *can* be combined via a `BitmapAnd`, but
that means scanning both indexes in full for their respective
predicates and intersecting the results — strictly more work than one
composite index that's already sorted to answer both conditions at
once. When columns are frequently filtered together, prefer one
composite index over two single-column ones.

## 4. Run it

```bash
.venv/Scripts/pytest lessons/03_composite_index -v
```

## 5. The gate

Same shape as lesson 02: correctness, plan (no `Seq Scan`, must use
`idx_orders_cust_status` — the planner may pick a plain `Index Scan`
or a `Bitmap Index Scan`/`Bitmap Heap Scan` pair, both count), and at
least an 8x speedup over the no-index baseline.

## 6. The teaching point

Column **order** in a composite index matters — it determines what
the index can be searched on efficiently (more on this in the next
lesson, on the left-prefix rule). For now: when a query always filters
on the same combination of columns, build one index over that
combination rather than one index per column.
