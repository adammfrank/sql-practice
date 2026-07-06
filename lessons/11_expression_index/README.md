# Lesson 11 — Expression (Functional) Indexes

A plain B-tree on `email` stores sorted raw `email` values — useless
when every lookup wraps the column in a function, like
`lower(email) = ...` for a case-insensitive match. The index is sorted
by `email`, not `lower(email)`, so Postgres can't use it. An
**expression index** fixes this: you index the *result of the
expression*, not the raw column.

## 1. The problem

Return the `id`s of `customers` where `lower(email) =
'user4242@example.com'` — a case-insensitive email match.

`customers` has 50,000 rows, `email` set to `user{id}@example.com`. A
plain index on `email` can't serve this; Postgres must scan every row
and lower-case its email to compare.

## 2. What to do

- In `indexes.sql`, create an **expression index** built over
  `lower(email)` — the exact expression the query filters by, not the
  bare `email` column (a plain column index won't be used here).
- Write the query above into `solution.sql`, returning `id`.

## 3. What you should see

```
Bitmap Heap Scan
  -> Bitmap Index Scan on <your expression index>
```

Postgres matches the `lower(email)` in your `WHERE` against the same
expression in the index definition and searches it like a plain column —
the index stores `(lower(email), row pointer)` pairs, sorted by the
computed value.

## 4. Why it's dramatically faster

Each `email` is unique, so `lower(email) = 'user4242@example.com'`
matches exactly **one row out of 50,000**. Measured: seq-scan baseline
~10–11ms; with the index, ~0.02–0.06ms — several hundred times faster.
The gate uses `ratio=8`, comfortably below what's achievable.

## 5. Run it

```bash
make test lessons/11_expression_index
```

## 6. The gate

Correctness, then no `Seq Scan` in the plan, then at least an 8x speedup
over the no-index baseline.

## 7. The teaching point

An index must be built on exactly the expression your queries filter by
— `lower(email)`, `date_trunc('day', created_at)`, `(price * quantity)`.
If a query consistently applies the same function to a column in
`WHERE`/`ORDER BY`, an expression index on that computed value restores
the logarithmic lookup instead of recomputing per row. (A generated
column that stores the value is the alternative for very hot
expressions, at the cost of changing the table's shape.)
