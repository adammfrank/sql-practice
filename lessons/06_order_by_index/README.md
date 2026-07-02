# Lesson 06 — Using an Index to Avoid a Sort

An index isn't only useful for `WHERE` filtering. If it's built in the
right column order, Postgres can also use it to read rows in the
order an `ORDER BY` wants, skipping a separate sort step entirely.
That matters most with `LIMIT`: if rows already come out of the index
in the right order, Postgres can stop as soon as it has enough of
them, instead of computing and sorting the full result set first.

## 1. The problem

```sql
SELECT id
FROM orders
WHERE customer_id = 4242
ORDER BY created_at DESC
LIMIT 10;
```

A customer's "10 most recent orders" — a very common access pattern.
Without help, Postgres has to find all of this customer's orders,
sort them by `created_at DESC`, and keep the top 10.

## 2. What to do

Create a composite index named `idx_orders_cust_created` on `orders`,
over `customer_id` first, then `created_at` — and store that second
column in **descending** order.

The column order matters in two ways here, stacking on what you
learned in lesson 03/04:

- `customer_id` first, so the index can seek directly to this
  customer's rows (the equality predicate).
- `created_at DESC` second, **and explicitly `DESC`**, so that within
  one customer's slice of the index, rows are *already* stored newest
  first — exactly the order `ORDER BY created_at DESC` wants. Without
  the explicit `DESC`, the index would store `created_at` ascending,
  and satisfying a `DESC` order would need either a backward index
  scan (works fine in Postgres, actually) or, if combined with other
  factors that defeat that, a sort. Building the index pre-sorted in
  the direction you query removes any doubt.

Then write the query in `solution.sql`.

## 3. Run it

```bash
.venv/Scripts/pytest lessons/06_order_by_index -v
```

## 4. The gate

This lesson checks row **order**, not just row identity — the test
passes `ordered=True` to `assert_rows_equal`, since `ORDER BY ...
LIMIT` queries are only correct if they return the *right* 10 rows in
the *right* sequence. (For this particular customer and column, there
are no duplicate `created_at` values, so the order is unambiguous.)

The plan check looks for the absence of a `Sort` node, plus
`uses_index="idx_orders_cust_created"`. No `Seq Scan` check this time
— the interesting failure mode here isn't "no index at all", it's
"index used for the `WHERE` but Postgres still sorts afterward."

## 5. The teaching point

When a query both filters and orders, look for one index that can do
both: a left-prefix match on the filtered column(s), followed by the
sorted column(s) in the same direction as the `ORDER BY`. Combined
with `LIMIT`, this turns "scan everything, sort it, take the top N"
into "walk the index in the order I already need, stop after N rows"
— one of the highest-leverage index designs for paginated or
"most recent N" queries.
