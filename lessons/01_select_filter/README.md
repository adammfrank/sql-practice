# Lesson 01 — SELECT/Filter Refresher

This lesson is a warm-up for the SQL muscles you'll lean on for the rest
of the dojo: joining a few tables together, filtering with `WHERE`, and
aggregating with `GROUP BY`. There's no indexing or query-plan work here
— the gate only checks that your query returns the right rows. Later
lessons will start grading plan shape and speed; this one is just about
getting the right *answer*.

## 1. The problem

Write a query that returns **total revenue per product category, for
orders with status `'paid'`**.

- Revenue for a line item is `quantity * price` from `order_items`.
- "Per category" means one row per `products.category`, with revenue
  summed across every paid order's line items in that category.
- Only include line items belonging to orders where `orders.status =
  'paid'` — ignore `'pending'`, `'cancelled'`, etc.

Relevant tables (see `dojo/schema.sql` for full definitions):

```sql
orders(id, customer_id, status, total, created_at)
order_items(id, order_id, product_id, quantity, price)
products(id, name, category, price, description, attributes)
```

Your result should have one row per distinct `category` with columns
`(category, revenue)`. Row order doesn't matter — the gate compares
results as sets, not sequences.

## 2. Where to write your answer

Open `solution.sql`. It currently contains a placeholder:

```sql
SELECT 1;
```

Replace it with your query. Don't edit `expected.sql` — that's the
answer key the gate checks you against, not something you're meant to
read before attempting the problem yourself (though nothing stops you;
this is a refresher, not a trick).

## 3. Run it

```bash
.venv/Scripts/pytest lessons/01_select_filter -v
```

With the placeholder still in `solution.sql`, this **fails** — `SELECT
1` returns one row, not one row per category, so
`grader.assert_rows_equal` reports a clear "expected N rows, got 1"
mismatch. That failure is expected until you fill in a real query.

## 4. The gate

`test_lesson.py` does exactly one thing this time:

```python
expected = lesson.fetch(conn, lesson.expected_sql)
actual = lesson.fetch(conn, lesson.solution_sql)
grader.assert_rows_equal(actual, expected, ordered=False)
```

It runs `expected.sql` and your `solution.sql` against the same
freshly-cloned database and checks the row sets match, ignoring order.
No `EXPLAIN`, no timing, no index requirement — correctness only. (And
indeed `indexes.sql` is empty for this lesson; you don't need to add
any indexes to solve it.)

## 5. What's next

Once you're comfortable joining and aggregating across these tables,
later lessons will start asking the same kind of question under a
"make it fast" constraint — that's where indexes, plan shapes, and
speed-ratio assertions come in.
