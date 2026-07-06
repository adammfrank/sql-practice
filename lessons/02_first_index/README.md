# Lesson 02 — Your First Index

`orders` has ~500,000 rows. So far every query you've run against it has
been a full table scan: Postgres reads every row, checks the `WHERE`
clause, and throws away the ones that don't match. That's fine for a
one-off report. It's not fine for a query you run thousands of times a
day looking up one customer's orders.

## 1. The problem

Write a query that returns a customer's orders — selecting `id`,
`total`, and `created_at` from `orders` for `customer_id = 4242`.

`customer_id` ranges from 1 to 50,000, spread roughly evenly across
500,000 orders — so this customer has on the order of 10 matching rows
out of half a million. A sequential scan has to visit all 500,000 to
find them. A B-tree index on `customer_id` lets Postgres jump straight
to the matching rows.

## 2. What to do

1. In `indexes.sql`, add the index that lets Postgres find this
   customer's rows without scanning the whole table. Write the
   `CREATE INDEX` yourself — no particular index name is required.
2. In `solution.sql`, write the query from the problem above.

Then run the test (below): it passes once the plan drops its `Seq Scan`
and the query clears the speed bar.

## 3. Run it

```bash
make test lessons/02_first_index
```

With the stub `indexes.sql` (no index) and stub `solution.sql`
(`SELECT 1`), this fails on the row-count check first. Once your query
is correct, the test will move on to checking the *plan* and the
*speed* — that's the new part starting with this lesson.

## 4. The gate

```python
expected = lesson.fetch(conn, lesson.expected_sql)
baseline = timing.cached_baseline(conn, lesson.slug, lesson.expected_sql)
lesson.apply_indexes(conn)
actual = lesson.fetch(conn, lesson.solution_sql)
grader.assert_rows_equal(actual, expected, ordered=False)
p = planmod.explain(conn, lesson.solution_sql)
grader.assert_plan(p, must_not_have=["Seq Scan"])
measured = timing.measure_execution_ms(conn, lesson.solution_sql)
grader.assert_faster_than_baseline(measured, baseline, ratio=8, floor_ms=2.0)
```

Three things have to be true:

- **Correctness** — same rows as `expected.sql`.
- **Plan shape** — no `Seq Scan` anywhere in the plan, which means
  Postgres is using your index instead. (Depending on how selective the
  predicate is, it might choose a plain `Index Scan` or a
  `Bitmap Index Scan` + `Bitmap Heap Scan` — both count, since both rely
  on the index.)
- **Speed** — your query must run at least 8x faster than the
  baseline (the same query measured with no index in place).

## 5. The teaching point

An index doesn't change *what* a query returns — only *how* Postgres
finds the matching rows. A B-tree index on `customer_id` stores sorted
`(customer_id, row pointer)` pairs, so looking up `customer_id = 4242`
becomes a logarithmic search instead of a linear scan of the whole
table. This is the single most common indexing decision you'll make in
real systems: "this column shows up in a lot of `WHERE` clauses on a
big table — index it."
