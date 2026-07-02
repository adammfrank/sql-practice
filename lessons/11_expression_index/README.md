# Lesson 11 — Expression (Functional) Indexes

A plain B-tree index on `email` stores sorted `email` values. That's
useless if every lookup wraps the column in a function first, like
`lower(email) = ...` for a case-insensitive match — the index is
sorted by the raw column, not by `lower(column)`, so Postgres can't
use it for that query no matter how selective the predicate is. An
**expression index** (also called a functional index) solves this: you
index the *result of the expression*, not the raw column.

## 1. The problem

```sql
SELECT id
FROM customers
WHERE lower(email) = 'user4242@example.com';
```

`customers` has 50,000 rows, one per `id` 1..50000, with `email` set
to `user{id}@example.com`. A plain index on `email` can't help this
query — `lower(email)` is a different value than `email` as far as a
B-tree comparison is concerned, so Postgres has no choice but to scan
every row, lower-case its email, and compare.

## 2. What to do

In `indexes.sql`, create an index named `idx_customers_lower_email` on
`customers`, over the *expression* `lower(email)` rather than the bare
`email` column.

Then write the query above into `solution.sql`.

## 3. What you should see in the plan

```
Bitmap Heap Scan
  -> Bitmap Index Scan on idx_customers_lower_email
```

Postgres matches the `lower(email)` expression in your `WHERE` clause
against the same expression stored in the index definition, and once
it recognizes they're identical, it can search the index just like it
would for a plain column — the index literally stores
`(lower(email), row pointer)` pairs, sorted by the computed value.

## 4. Why this one is dramatically faster

`email` is `user{id}@example.com` for every `id` from 1 to 50,000 —
each value is unique, so `lower(email) = 'user4242@example.com'`
matches exactly **one row out of 50,000**. That's about as selective
as a predicate gets. Measured on the seeded template: the sequential
scan baseline runs ~10-11ms; with the expression index in place, the
same query runs in a fraction of a millisecond (~0.02-0.06ms) — several
hundred times faster. The gate here uses `ratio=8`, comfortably below
what's actually achievable, so it's a reliable floor rather than a
tight one.

## 5. Run it

```bash
.venv/Scripts/pytest lessons/11_expression_index -v
```

## 6. The gate

Correctness, then the plan must not contain a `Seq Scan` and must use
`idx_customers_lower_email`, then at least an 8x speedup over the
no-index baseline.

## 7. The teaching point

An index has to be built on exactly the expression your queries filter
by. `lower(email)`, `date_trunc('day', created_at)`, `upper(name)`,
even something like `(price * quantity)` — if a query's `WHERE` or
`ORDER BY` consistently applies the same function or computation to a
column, an expression index on that computed value turns the same
kind of logarithmic lookup you'd get from a plain B-tree index into
something usable, instead of forcing Postgres to recompute the
expression for every row in the table. The alternative — a computed /
generated column that stores the value directly — is sometimes
cleaner for very hot expressions, but an expression index gets you the
same query-time benefit without changing the table's visible shape at
all.
