# Lesson 06 — Using an Index to Avoid a Sort

An index isn't only useful for `WHERE` filtering. If it's built in the right
column order, Postgres can also use it to read rows in the order an `ORDER BY`
wants, skipping a separate sort step entirely. That matters most with `LIMIT`:
if rows already come out of the index in the right order, Postgres can stop as
soon as it has enough of them, instead of computing and sorting the full result
set first.

## 1. The problem

Return the `id`s of `customer_id = 4242`'s ten most recent orders — filtered to
that customer, ordered by `created_at` descending, limited to 10 rows.

A customer's "10 most recent orders" — a very common access pattern. Without
help, Postgres has to find all of this customer's orders, sort them by
`created_at DESC`, and keep the top 10.

## 2. What to do

In `indexes.sql`, build one index that lets Postgres return these rows _already
in the order the query asks for_, so it can skip the sort and stop after the
first 10.

Then write the query in `solution.sql`.

## 3. Run it

```bash
make test lessons/06_order_by_index
```

## 4. The gate

This lesson checks row **order**, not just row identity — the test passes
`ordered=True` to `assert_rows_equal`, since `ORDER BY ...
LIMIT` queries are
only correct if they return the _right_ 10 rows in the _right_ sequence. (For
this particular customer and column, there are no duplicate `created_at` values,
so the order is unambiguous.)

The plan check looks for the absence of a `Sort` node (it also forbids a
`Seq Scan`). The interesting failure mode here isn't "no index at all" — it's
"index used for the `WHERE` but Postgres still sorts afterward."

## 5. The teaching point

When a query both filters and orders, look for one index that can do both: a
left-prefix match on the filtered column(s), followed by the sorted column(s) in
the same direction as the `ORDER BY`. Combined with `LIMIT`, this turns "scan
everything, sort it, take the top N" into "walk the index in the order I already
need, stop after N rows" — one of the highest-leverage index designs for
paginated or "most recent N" queries.
