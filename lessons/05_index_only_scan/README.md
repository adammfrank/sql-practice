# Lesson 05 — Covering Indexes and Index Only Scan

Every lesson so far has used an index to *find* matching rows, then
gone back to the table heap to fetch the actual column values (an
`Index Scan` or `Bitmap Heap Scan` does this "heap fetch" step). If
every column the query needs is already sitting in the index itself,
Postgres can skip the heap fetch entirely. That's an **Index Only
Scan**.

## 1. The problem

```sql
SELECT customer_id, total
FROM orders
WHERE customer_id BETWEEN 1000 AND 1100;
```

This needs two columns: `customer_id` (in the `WHERE` and the
`SELECT`) and `total` (only in the `SELECT`). A plain index on
`customer_id` would find the matching rows fine, but Postgres would
still have to visit the heap for every row just to read `total`.

## 2. What to do

In `indexes.sql`, create an index named `idx_orders_cust_incl` on
`customer_id` that also *carries* `total` as a non-key payload column,
using an `INCLUDE` clause.

`INCLUDE` columns aren't part of the B-tree search key (you still
can't search by `total` with this index) — they're just extra data
stored alongside each index entry so queries that only *read* them
don't need the heap. Then write the query in `solution.sql`.

## 3. The VACUUM catch

An Index Only Scan has one more requirement beyond "the index has all
the columns I need": Postgres also has to be sure that the row version
pointed to by each index entry is visible to your transaction *without
checking the heap*. It tracks this in the table's **visibility map** —
a bitmap of which heap pages are "all visible" (no recent updates/
deletes to worry about). That map is only brought up to date by
`VACUUM`.

Right after `CREATE INDEX`, the visibility map may still be stale, so
even with a perfect covering index Postgres might fall back to a
regular `Index Scan` (with heap fetches) until a `VACUUM` runs. This
test handles that for you — it runs `VACUUM orders` on a separate
autocommit connection after applying your `indexes.sql` (`VACUUM`
can't run inside a transaction block, which is what the normal test
connection is in). In your own database, you'd either wait for
autovacuum to catch up or run `VACUUM` yourself after creating a new
covering index.

## 4. Run it

```bash
.venv/Scripts/pytest lessons/05_index_only_scan -v
```

## 5. The gate

This lesson's plan check is stricter than earlier ones: it requires
`must_have=["Index Only Scan"]` (not just "uses an index") — that's
the entire point of the `INCLUDE` clause. It also still requires no
`Seq Scan`, correctness, and an 8x speedup over baseline.

## 6. The teaching point

A "covering index" is one that contains every column a query needs, so
the query never touches the table heap — only the (usually much
smaller, more cache-friendly) index. `INCLUDE` lets you add payload
columns to a B-tree without making them part of the sort key, which
keeps the index's search behavior simple while still making it
"cover" more queries. The tradeoff: every `INCLUDE`d column makes the
index bigger and adds a little overhead to every write — covering
indexes are a deliberate choice for hot, read-heavy queries, not a
free upgrade you apply everywhere.
