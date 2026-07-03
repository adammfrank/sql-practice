# Lesson 04 — The Left-Prefix Rule

In the previous lesson you built `idx_orders_cust_status` on
`(customer_id, status)` to speed up `customer_id = 4242 AND status =
'paid'`. That index already exists in this lesson's `indexes.sql`.
This lesson asks a query that only filters on `status`, and the
existing index turns out not to help.

## 1. The problem

Return the `id`s of `orders` where `status = 'shipped'`.

## 2. Why `idx_orders_cust_status` doesn't help

A B-tree composite index on `(customer_id, status)` is physically
sorted **first by `customer_id`, then by `status` within each
`customer_id`**. Think of a phone book sorted by (last name, first
name): if you only know someone's first name, you can't binary-search
the book — "Alice" is scattered across every last-name bucket. You'd
have to read the whole book.

Same here: `status = 'shipped'` rows are scattered across every
`customer_id` bucket in the index. Postgres can only use a composite
index efficiently for predicates that include a **left prefix** of its
columns — `customer_id` alone, or `customer_id AND status` together.
A predicate on `status` alone, with no `customer_id` condition, can't
use this index to narrow anything down (Postgres would have to scan
the entire index, which is no better than scanning the table itself —
so the planner just does a `Seq Scan` instead).

Run the test now, with only `idx_orders_cust_status` in place and a
correct query in `solution.sql`, and check the plan: you'll see a
`Seq Scan` on `orders`, not an index scan.

## 3. What to do

Add another index in `indexes.sql` that will let this query beat the
full `Seq Scan`. Keep the existing `idx_orders_cust_status` line in
place — you're **adding** an index, not replacing it. (In a real
system you'd reconsider whether you need both; here the point is to see
for yourself that the composite index can't stand in for its second
column.)

Then write the query in `solution.sql` and run the test — it tells you
whether your index did the job.

## 4. Run it

```bash
.venv/Scripts/pytest lessons/04_left_prefix -v
```

## 5. The gate

Correctness, plan (no `Seq Scan`), and a speedup over the no-index
baseline. The **plan check is the real gate
here** — it's what forces you to build the right index. The required
ratio (1.5x) is much lower than earlier lessons and is only a secondary
sanity floor. `status` has only four distinct values, and `'shipped'`
matches roughly 83,000 of the 500,000 rows (~17%) — not very selective.
A `Bitmap Index Scan` over that many matching rows still has to fetch a
large fraction of the table's pages, so it only modestly beats a
`Seq Scan` (measured ~1.5x on the seeded data, ~26ms → ~16ms), not
dramatically. That's a real, useful lesson on its own: **indexes help
most when the predicate is selective; on a low-cardinality column
matched against a large fraction of rows, the win shrinks** — Postgres
may even choose a `Seq Scan` over the index for a less selective value.

## 6. The teaching point

A composite index `(a, b)` can serve: `WHERE a = ?`, `WHERE a = ? AND
b = ?`, and range/sort queries on `a` — anything that uses a
**left-anchored prefix** of the indexed columns. It generally cannot
efficiently serve `WHERE b = ?` alone. If two different query shapes
need to filter independently on different columns, you usually need
separate indexes (or a different column order) for each access
pattern — one composite index doesn't make every column in it equally
searchable on its own.
