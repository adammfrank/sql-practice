# Lesson 10 — Partial Indexes

Every index you've built so far indexes *every row* in the table. But
you frequently only ever query for a narrow, well-known slice of a
table's rows — "orders still waiting to ship," "users who haven't
verified their email," "unprocessed jobs." Building a full index to
serve a query that only ever touches a slice of the table wastes disk
space and slows down every `INSERT`/`UPDATE` that has to maintain rows
outside that slice too. A **partial index** — an index with a `WHERE`
clause of its own — covers only the rows you actually query.

## 1. The problem

```sql
SELECT id
FROM orders
WHERE status = 'pending';
```

`orders` has ~500,000 rows. A naive fix would be `CREATE INDEX ON
orders (status)` — a full B-tree over every order regardless of
status. That works, but it indexes ~416,000 rows you'll never look up
this way (`paid`, `shipped`, `cancelled` orders) just to serve lookups
against the ~84,000 `pending` ones.

## 2. What to do

In `indexes.sql`, create a **partial index**: a B-tree that only
covers rows matching `status = 'pending'`.

```sql
CREATE INDEX idx_orders_pending ON orders(id) WHERE status='pending';
```

Note the index is on `id` (not `status`) — once the `WHERE` clause has
already narrowed things down to pending orders, there's nothing left
to search *by*, so the index just needs to give Postgres a compact
list of matching row locations. This also means a query like `SELECT
id FROM orders WHERE status = 'pending'` can potentially be answered
as an **index-only scan** — no heap access needed at all, since `id`
is the only column requested and it's sitting right there in the
index. Then write the query above into `solution.sql`.

## 3. What you should see in the plan

```
Index Only Scan using idx_orders_pending
```

Postgres recognizes that your query's `WHERE status = 'pending'`
clause exactly matches the index's own `WHERE` clause, so it can use
the index directly — no recheck against the heap needed for the
`status` predicate at all (though it may still need to check tuple
visibility, hence "Index Only Scan" rather than promising zero heap
access in all cases).

## 4. A note on selectivity and the ratio you'll actually see

You might expect `pending` to be a rare status — a handful of orders
mid-checkout, most already `paid`. It isn't, in this seed data:
`dojo/seed.py` picks status from `["pending", "paid", "paid", "paid",
"shipped", "cancelled"]`, so `pending` lands on about 1 in 6 orders —
measured, 83,531 of 500,000 (~16.7%). That's the same
moderate-selectivity territory that limited the speedups in lessons 04
and 09.

Measured across repeated clone-and-time trials against the seeded
template, the partial index runs **2.4x-4.3x** faster than the
sequential-scan baseline (minimum observed: 2.4x, under concurrent
system load). This lesson's gate uses `ratio=2`, set below that
measured floor so it's a real gate without being flaky — noticeably
lower than the brief's originally suggested `ratio=10`, which isn't
achievable at this selectivity (the same ceiling that forced lessons
04 and 09 down). The plan assertion (no `Seq Scan`, must use
`idx_orders_pending`) is the primary teaching gate here; the speed
ratio is a secondary floor.

## 5. The real payoff: index size, not just query speed

The speedup above undersells partial indexes, because the *bigger*
practical benefit is size — and size affects both storage and, more
importantly, the cost of maintaining the index on every write.
Measured directly on this seeded data with `pg_relation_size`:

| Object | Size |
|---|---|
| `orders` table | 34 MB |
| Partial index (`WHERE status='pending'`, ~84K rows) | **1,848 KB** |
| Full index on the same column, all ~500K rows (hypothetical, for comparison) | 11 MB |

The partial index is roughly **6x smaller** than a full index would
be over the same column — because it only stores entries for the ~1/6
of rows it actually needs to. In a real system where `orders` also
gets a steady stream of `INSERT`s and `UPDATE`s, that's 5/6 fewer
index entries to write and maintain on every change to a non-pending
order. If your query pattern only ever touches a known slice of a
table, a partial index gives you the lookup speed of an index at a
fraction of the size and write cost of indexing everything.

## 6. Run it

```bash
.venv/Scripts/pytest lessons/10_partial_index -v
```

## 7. The gate

Correctness, then the plan must not contain a `Seq Scan` and must use
`idx_orders_pending`, then at least a 2x speedup over the no-index
baseline (see step 4 for why 2x, not the more dramatic ratios from
earlier lessons).

## 8. The teaching point

A partial index trades generality for size and maintenance cost: it
can only serve queries whose `WHERE` clause is provably a subset of
the index's own `WHERE` clause (Postgres checks this at plan time), so
it's not a general-purpose tool — it's a scalpel for exactly the
narrow, well-known access pattern you tell it about up front. When
that pattern is "always filtering by a status/flag/tier column to a
small known set of values you actually query for," a partial index is
almost always the right call over a full index on that column.
