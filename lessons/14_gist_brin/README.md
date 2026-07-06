# Lesson 14 — BRIN for Huge, Naturally-Ordered Tables (and GiST, in theory)

`events` is the biggest table here: 3,000,000 rows, one per second,
strictly increasing in `ts` — an append-only log inserted in time order.
A B-tree on `ts` works but is overkill: a full sorted structure with an
entry per row. **BRIN** (Block Range INdex) suits exactly this — a huge
table whose column correlates with physical row order — giving most of
the query speedup at a tiny fraction of the size.

## 1. The problem

Count the rows in `events` whose `ts` falls in the one-day window
`ts >= '2023-11-01' AND ts < '2023-11-02'`.

The seed data fixes `ts` at generation time, spanning ~2023-10-11 to
2023-11-14; this window sits inside that range and matches ~86,400 rows.

## 2. What to do

- In `indexes.sql`, add a **BRIN index** on `ts` (`USING brin (...)`).
- Write the query above into `solution.sql` — a `count(*)`.

## 3. What you should see

```
Aggregate
  -> Bitmap Heap Scan
       -> Bitmap Index Scan on <your BRIN index>
```

BRIN doesn't index rows. It divides the table into consecutive **block
ranges** (128 pages by default) and stores each range's min/max `ts`. A
range whose min/max can't overlap the window is skipped without reading
its rows. This only works because `ts` is *physically* sorted, so
consecutive pages hold narrow, non-overlapping timestamp ranges — random
order would make every range span the whole table.

## 4. The real point: index size

Measured with `pg_relation_size`:

| Object | Size |
|---|---|
| `events` table (3,000,000 rows) | 317 MB |
| BRIN index on `ts` | **32 KB** |
| B-tree on `ts` (for comparison) | 64 MB |

~2,000x smaller, because it stores one summary per block range, not one
entry per row — essentially free to maintain on every insert. The
tradeoff is precision: BRIN only rules out whole ranges, so it rechecks
every row in a range it can't rule out (hence `Bitmap Heap Scan`, not an
index-only answer).

## 5. A note on the speedup

BRIN runs about **4.3–6.9x** faster than the seq scan here, but with more
run-to-run variance than a B-tree lookup — a raw scan of 3M rows already
benefits from parallel workers and readahead. The gate uses `ratio=4`.

## 6. Run it

```bash
make test lessons/14_gist_brin
```

## 7. The gate

Correctness, then the plan must contain a `Bitmap Index Scan`, then at
least a 4x speedup over the no-index baseline.

## 8. GiST (reading only — no gate)

BRIN and B-tree both assume an ordered scalar. **GiST** (Generalized
Search Tree) handles data with no natural sort order — geometry, or
**ranges as values** (`tstzrange`, `int4range`), where the question is
"does this range overlap that range" (the `&&` operator) rather than "is
this value between X and Y." This schema has no range column, but picture
a bookings table with a `during tstzrange` instead of a single `ts`: a
GiST index on it makes overlap queries indexable, which no B-tree or BRIN
can do (there's no sort order that turns "A overlaps B" into a
comparison). GiST organizes ranges into a tree whose nodes bound their
children, pruning subtrees that can't overlap the query — like BRIN's
block-range pruning, but as a real tree over non-scalar data.

## 9. The teaching point

Match the index to how your data compares: **B-tree** for point/range on
an ordered scalar; **BRIN** for the same on a huge table where the column
correlates with physical order, trading precision for a tiny index;
**GIN** for "does this multi-valued thing contain X" (lexemes, JSONB,
arrays); **GiST** for non-scalar data like ranges and geometry with no
single sort order. Recognizing which situation you're in is most of the
job of picking the right index.
