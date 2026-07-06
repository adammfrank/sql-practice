# Lesson 10 — Partial Indexes

Every index so far covers *every row* in the table. But you often only
query a narrow, well-known slice — "orders still pending," "unverified
users," "unprocessed jobs." A full index over the whole table wastes
space and slows every write that maintains rows outside that slice. A
**partial index** — one with its own `WHERE` clause — covers only the
rows you actually query.

## 1. The problem

Return the `id`s of `orders` where `status = 'pending'`.

`orders` has ~500,000 rows. A plain B-tree on `status` works but indexes
all ~416,000 non-pending rows too, just to serve lookups against the
~84,000 pending ones.

## 2. What to do

- In `indexes.sql`, create a **partial index**: a B-tree with a
  `WHERE status = 'pending'` clause of its own, so it covers only that
  slice.
- Index the `id` column the query returns. Once the partial `WHERE` has
  narrowed to pending rows, `id` is all that's left to return, so this
  lets Postgres answer via an **index-only scan** (no heap access).
- Write the query above into `solution.sql`, returning `id`.

## 3. What you should see

```
Index Only Scan using <your partial index>
```

Postgres recognizes the query's `WHERE status = 'pending'` matches the
index's own `WHERE`, so it uses the index directly with no heap recheck
of the predicate.

## 4. Selectivity and size

`pending` isn't rare here — `dojo/seed.py` makes it ~1 in 6 orders
(measured 83,531 / 500,000). At that selectivity the query runs about
**2.4–4.3x** faster than a seq scan, so the gate uses `ratio=2`; the
no-`Seq Scan` plan check is the primary gate.

The bigger payoff is size — and therefore write cost. Measured with
`pg_relation_size`:

| Object | Size |
|---|---|
| `orders` table | 34 MB |
| Partial index (`WHERE status='pending'`, ~84K rows) | **1,848 KB** |
| Full index on `status`, all ~500K rows | 11 MB |

~6x smaller, because it only stores the ~1/6 of rows it needs — 5/6
fewer index entries to maintain on every write to a non-pending order.

## 5. Run it

```bash
make test lessons/10_partial_index
```

## 6. The gate

Correctness, then no `Seq Scan` in the plan, then at least a 2x speedup
over the no-index baseline.

## 7. The teaching point

A partial index trades generality for size: it can only serve queries
whose `WHERE` is provably a subset of the index's own `WHERE` (Postgres
checks at plan time). It's a scalpel for one narrow, known access
pattern — ideal when you always filter a status/flag/tier column to a
small set of values you actually query.
