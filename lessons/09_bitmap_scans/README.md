# Lesson 09 — Bitmap Scans and Combining Indexes with `BitmapAnd`

Lesson 03 taught you that two single-column indexes are usually worse
than one composite index for a query that always filters on both
columns together — because combining them means scanning both indexes
in full and intersecting the results. This lesson shows you that
combination mechanism directly: the **bitmap index scan**, and how
Postgres uses it to `AND` two single-column indexes together when
that turns out to be the best available option.

## 1. The problem

```sql
SELECT id
FROM orders
WHERE status = 'pending'
  AND created_at >= '2023-09-15'::timestamptz;
```

Note the fixed cutoff date: this course's seed data is generated with
`created_at` timestamps spanning roughly November 2022 to November
2023 (deterministic, fixed at seed time — it doesn't shift with the
calendar). The brief for this lesson describes `now() - interval '30
days'`, but "30 days before today" would fall years after this
dataset ends and match zero rows — so this lesson pins the cutoff to
`'2023-09-15'`, a fixed date inside the seeded range, chosen
specifically so the two predicates below have *comparable*
selectivity (see step 4 for why that's the detail that matters here).
In your own database, you'd use the real `now() - interval '30 days'`
against real, continuously-arriving data.

Two independent conditions, each only moderately selective on its
own:

- `status = 'pending'` matches roughly 1 in 6 orders.
- `created_at >= '2023-09-15'` matches roughly 1 in 6 orders too.

Together, roughly 1 in 36 orders match both — selective as a pair,
but neither condition alone narrows things down much.

## 2. What to do

In `indexes.sql`, create **two separate single-column indexes** —
deliberately not a composite one this time:

```sql
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_created_at ON orders (created_at);
```

Then write the query above into `solution.sql`.

## 3. What you should see in the plan

```
Bitmap Heap Scan
  -> BitmapAnd
       -> Bitmap Index Scan on idx_orders_status
       -> Bitmap Index Scan on idx_orders_created_at
```

Each `Bitmap Index Scan` walks one index and builds an in-memory
**bitmap** — one bit per heap page (or per row, depending on size),
marking which pages might contain a matching row. `BitmapAnd` takes
two such bitmaps and intersects them with a bitwise AND, cheaply,
in memory — no heap access needed for the intersection itself. Only
then does `Bitmap Heap Scan` visit the heap, and only for the pages
the intersected bitmap says are worth visiting, rechecking the actual
row conditions once it gets there (bitmaps are page-granular, so a
page can be flagged even if only one row on it matches).

## 4. Why the planner reaches for `BitmapAnd` *here* specifically

This is the detail that makes this query a good example, and it's
also why the exact cutoff date matters. `BitmapAnd` is worth it only
when:

- **Neither single index is selective enough on its own** to just use
  it and recheck the other condition row-by-row. If `status =
  'pending'` matched 50 rows, Postgres would just use
  `idx_orders_status` alone and filter the date condition during the
  heap recheck — no need to consult the other index at all.
- **Both indexes are still meaningfully selective together.** If one
  condition matched almost the whole table, intersecting bitmaps
  wouldn't save much over just using the other index alone.

`status = 'pending'` (~1/6 of rows) and `created_at >= '2023-09-15'`
(~1/6 of rows, with this specific cutoff) sit right in that middle
ground: each one, alone, is too weak to be worth using by itself, but
combined they're worth intersecting. That's a narrower window than
you might expect — nudge the cutoff date substantially earlier or
later and one predicate becomes either too selective (planner just
uses that index alone) or not selective enough (planner falls back to
a sequential scan). This sensitivity is itself the lesson: `BitmapAnd`
isn't the default outcome of "add two indexes," it's a specific
middle-ground case the planner reaches for only when the numbers work
out that way.

## 5. A note on the speedup you'll actually see

Don't expect the dramatic 8x-plus speedups from earlier lessons here.
The `orders` table is small enough (a few tens of MB) that a full
sequential scan of it is already cheap — most of the table's pages
fit in memory, and reading them all in physical order is fast. Query
patterns matching a comparably-large slice of a small-to-medium table
are exactly the case where bitmap scans help the *least* in relative
terms, even though they're still a real, measurable improvement.
Measured on this dataset, `BitmapAnd` reliably runs about **1.6-2x**
faster than the sequential-scan baseline — real, but nowhere near the
order-of-magnitude wins you get when a predicate is highly selective
(as in lessons 02-06). This lesson's gate is set to `ratio=1.5` to
match what's actually achievable here; don't be surprised that it's
lower than other lessons' gates.

## 6. Run it

```bash
.venv/Scripts/pytest lessons/09_bitmap_scans -v
```

## 7. The gate

Correctness, then the plan must contain both `Bitmap Heap Scan` and
`BitmapAnd` (confirming the planner actually combined the two
indexes, not just picked one), then at least a 1.5x speedup over the
no-index baseline (see the note in step 5 for why this ratio is lower
than earlier lessons).

## 8. The teaching point

A bitmap scan is Postgres's mechanism for combining multiple indexes
on the fly, when no single index (composite or otherwise) already
covers the query. It's strictly more work than one well-designed
composite index covering the same predicates — building two bitmaps
and intersecting them costs more than one sorted structural lookup —
but it's a genuinely useful fallback for ad hoc combinations of
filters you didn't (or couldn't) build a matching composite index for
in advance. If you find yourself staring at a `BitmapAnd` in
production for a query pattern that runs constantly, that's usually a
signal to go build the matching composite index, the way lesson 03
did — `BitmapAnd` is what the planner reaches for when it has to
combine indexes at query time; a composite index does the same job
once, in advance, at index-build time.
