# Lesson 14 — BRIN for Huge, Naturally-Ordered Tables (and GiST, in theory)

`events` is the biggest table in this dataset: 3,000,000 rows, one per
second, strictly increasing in `ts` — a realistic shape for an
event-log / telemetry table that's append-only and always inserted in
time order. A B-tree index on `ts` would work, but it's overkill: it
builds a full sorted structure with an entry for every one of 3
million rows. **BRIN** (Block Range INdex) is built for exactly this
situation — huge tables where a column's values correlate with
physical row order — and gets you most of the query speedup at a tiny
fraction of the size and maintenance cost.

## 1. The problem

Count the rows in `events` whose `ts` falls in the one-day window
`ts >= '2023-11-01' AND ts < '2023-11-02'`.

This course's seed data fixes `events.ts` at generation time
(`dojo/seed.py`: `base = 1_700_000_000`, 3,000,000 rows, one per
second) — confirmed directly against the seeded template:
`min(ts) = 2023-10-11 04:53:21 UTC`, `max(ts) = 2023-11-14 22:13:20
UTC`, about 35 days. The one-day window above (`2023-11-01` to
`2023-11-02`) falls safely inside that range and matches about one
day's worth of rows (~86,400, one per second).

## 2. What to do

In `indexes.sql`, add a BRIN index named `idx_events_ts_brin` on
`events`, over the `ts` column — use a `USING brin (...)` clause.

Then write the query above into `solution.sql`.

## 3. What you should see in the plan

```
Aggregate
  -> Bitmap Heap Scan
       -> Bitmap Index Scan on idx_events_ts_brin
```

BRIN doesn't index individual rows. It divides the table into
consecutive **block ranges** (a run of physical table pages — 128
pages by default) and, for each range, stores a small summary:
"every `ts` value in this range of pages falls between MIN and MAX."
A query for `ts` in some window can then skip any block range whose
MIN/MAX summary doesn't overlap the window, without looking at the
rows inside it at all. This only pays off because `ts` is *physically*
sorted — rows are inserted in `ts` order, so consecutive pages
naturally hold narrow, mostly non-overlapping timestamp ranges. If
`ts` values were scattered randomly across the table, every block
range's MIN/MAX would span almost the whole table and BRIN couldn't
rule anything out.

## 4. The real point: index size

This is where BRIN earns its place in the toolbox. Measured directly
on the seeded `events` table with `pg_relation_size`:

| Object | Size |
|---|---|
| `events` table (3,000,000 rows) | 317 MB |
| BRIN index on `ts` | **32 KB** |
| B-tree index on `ts` (hypothetical, for comparison) | 64 MB |

The BRIN index is **roughly 2,000x smaller** than a B-tree over the
same column would be — 32 KB versus 64 MB — because it stores one
summary per block range (a handful of bytes) instead of one entry per
row. For an append-heavy table this large, that's the difference
between an index that's essentially free to maintain on every insert
and one that adds real, ongoing write overhead. The tradeoff is
precision: BRIN can only rule out whole block ranges, so it still has
to recheck every row in a range it can't rule out (hence `Bitmap Heap
Scan`, not an index-only answer) — it's a coarser filter than a
B-tree, in exchange for being nearly free.

## 5. On the speedup, and why it's noisier than earlier lessons

Measured across repeated clone-and-time trials on the seeded template,
the BRIN-indexed query ran **4.3x-6.9x** faster than the sequential
scan baseline (minimum observed: 4.33x). That's a real, solid
speedup, but with more trial-to-trial variance than the B-tree lookups
in earlier lessons — a raw sequential scan of 3,000,000 rows already
benefits from Postgres's parallel workers and sequential I/O
readahead, and a BRIN bitmap scan's win depends on how cleanly the
block ranges partition the requested window, so the margin moves
around more between runs. This lesson's gate uses `ratio=4`, set below
the measured floor, rather than the brief's suggested `ratio=5`, which
occasionally isn't cleared given that variance.

## 6. Run it

```bash
.venv/Scripts/pytest lessons/14_gist_brin -v
```

## 7. The gate

Correctness, then the plan must contain a `Bitmap Index Scan` and use
`idx_events_ts_brin`, then at least a 4x speedup over the no-index
baseline.

## 8. GiST (reading only — no separate gate)

BRIN and B-tree both assume you're searching for a *point* or *range*
on an ordered scalar. **GiST** (Generalized Search Tree) is Postgres's
index type for genuinely more complex data: things with no single
natural sort order, like geometric shapes, or **ranges as
first-class values** (`tstzrange`, `int4range`, etc.), where the
query you actually want to ask is "does this range overlap that
range" rather than "is this value between X and Y."

This schema doesn't have a native range column to demonstrate that on
directly, so picture a table that did: a bookings/reservations table
with a `during` column of type `tstzrange` instead of a single `ts`
timestamp. A GiST index on that `during` column would make overlap
queries indexable — letting you ask which rows' `during` range overlaps
(the `&&` operator) some target range, such as the first two days of
November.

The `&&` "overlaps" operator has no B-tree or BRIN equivalent — there's
no single sort order that makes "does range A overlap range B" a
simple comparison. GiST organizes ranges (or shapes) into a tree where
each node bounds the entries beneath it, so a search can prune whole
subtrees that provably can't overlap the query range, similar in
spirit to how BRIN prunes block ranges by MIN/MAX, but structured as a
real tree instead of a flat list of summaries, and generalized to
data with no scalar order at all. If you ever model "reservation
periods," "meeting time slots," or "geographic regions" as literal
range/geometric columns instead of a pair of `start`/`end` scalars,
GiST is the index type that makes overlap and containment queries on
them efficient.

## 9. The teaching point

Match the index type to what "correlates" or "compares" about your
data: B-tree for point/range lookups on a scalar with no particular
physical order; BRIN for the same kind of lookup when the column
happens to correlate with physical row order on a huge table, trading
precision for a dramatically smaller index; GIN for "does this
multi-valued thing contain X" (full-text lexemes, JSONB keys, arrays);
GiST for genuinely non-scalar data like ranges and geometry where
there's no single sort order to exploit at all. Reaching for a B-tree
by default works until the table is either too big to index cheaply
(BRIN's case) or the data itself doesn't fit a linear order (GIN's and
GiST's case) — recognizing which situation you're in is most of the
job of picking the right index.
