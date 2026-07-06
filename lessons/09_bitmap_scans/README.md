# Lesson 09 — Bitmap Scans and Combining Indexes with `BitmapAnd`

Lesson 03 showed that two single-column indexes are usually worse than
one composite index for a query that always filters on both columns.
This lesson shows the mechanism Postgres uses when it *does* combine two
separate indexes: the **bitmap index scan**, intersected with
`BitmapAnd`.

## 1. The problem

Return the `id`s of `orders` where `status = 'pending'` **and**
`created_at >= '2023-09-15'::timestamptz`.

The cutoff is a fixed date because the seed data's `created_at` spans a
fixed window (~Nov 2022–Nov 2023) and doesn't move with the calendar;
`'2023-09-15'` is chosen so both predicates have comparable
selectivity. Each condition alone matches ~1 in 6 orders; together ~1 in
36 — selective as a pair, weak individually. That middle ground is
exactly when `BitmapAnd` wins: neither index is selective enough to use
alone, but both are worth intersecting.

## 2. What to do

- In `indexes.sql`, create **two separate single-column indexes** — one
  on `status`, one on `created_at`. Deliberately *not* one composite
  index: the point is to watch Postgres combine them.
- Write the query above into `solution.sql`, returning `id`.

## 3. What you should see

```
Bitmap Heap Scan
  -> BitmapAnd
       -> Bitmap Index Scan on <your status index>
       -> Bitmap Index Scan on <your created_at index>
```

Each `Bitmap Index Scan` walks one index and builds an in-memory bitmap
of candidate heap pages; `BitmapAnd` intersects the two bitmaps with a
cheap bitwise AND; only then does `Bitmap Heap Scan` visit the surviving
pages, rechecking the row conditions there (bitmaps are page-granular).

## 4. A note on the speedup

Don't expect the 8x+ wins of earlier lessons. `orders` is small enough
(tens of MB) that a full seq scan is already cheap, so a moderately
selective bitmap scan only runs about **1.6–2x** faster here. The gate
uses `ratio=1.5` to match.

## 5. Run it

```bash
make test lessons/09_bitmap_scans
```

## 6. The gate

Correctness, then the plan must contain both `Bitmap Heap Scan` and
`BitmapAnd` (proving the two indexes were combined), then at least a
1.5x speedup over the no-index baseline.

## 7. The teaching point

A bitmap scan is how Postgres combines multiple indexes on the fly when
no single index covers the query. It's more work than one well-designed
composite index — building and intersecting two bitmaps vs. one sorted
lookup — so a `BitmapAnd` on a query pattern that runs constantly is
usually a signal to go build the matching composite index (lesson 03).
