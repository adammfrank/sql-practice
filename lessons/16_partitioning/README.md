# Lesson 16 — Declarative Partitioning and Partition Pruning

Indexes speed lookups *inside* a table. **Partitioning** splits the
table itself into smaller physical pieces, each holding a disjoint slice
of the data, so the planner can skip entire pieces that can't contain
matching rows.

## 1. The problem

`events` has 3,000,000 rows spanning ~2023-10-11 to 2023-11-14. A
`count(*)` for one month still considers the whole table, because
`events` is one physical relation. An index on `ts` would help, but the
heap still mixes months together and grows forever — and archiving or
dropping *part* of a plain table is awkward.

## 2. Declarative partitioning

You declare a parent table `PARTITION BY RANGE (ts)` and attach child
partitions that each own a key range:

- **Parent**: `CREATE TABLE ... PARTITION BY RANGE (ts)`, with the same
  columns as `events` (`id bigint`, `customer_id bigint`,
  `event_type text`, `payload jsonb`, `ts timestamptz`). It holds no rows
  itself.
- **Child**: `CREATE TABLE <child> PARTITION OF <parent> FOR VALUES FROM
  (<low>) TO (<high>)`. Bounds are half-open `[low, high)`, so adjacent
  partitions share a boundary value without overlapping.

Rows inserted into the parent route automatically to the child whose
range covers their `ts`. Each partition is an ordinary table with its own
storage.

## 3. What to do

In `indexes.sql`, write the DDL:

- a parent table named **`events_part`**, `PARTITION BY RANGE (ts)`, with
  the columns listed above;
- two monthly partitions named **`events_p_2023_10`** and
  **`events_p_2023_11`**, as half-open ranges covering the data's full
  span (all of 2023-10 and 2023-11). Names must start with `events_p_` —
  the gate counts scanned partitions by that prefix;
- an `INSERT ... SELECT` from `events` to populate it (rows route
  automatically).

(This is one-time DDL + backfill, like every earlier `indexes.sql`, just
heavier — it takes a few seconds.)

In `solution.sql`, write the same one-month query as `expected.sql` but
against `events_part`: a `count(*)` over
`ts >= '2023-11-01' AND ts < '2023-12-01'`.

## 4. Partition pruning

`EXPLAIN` your query. Because the `WHERE` is a constant range comparable
to each partition's declared bounds, the planner proves at plan time that
`events_p_2023_10` can't match and drops it — only `events_p_2023_11` is
scanned. That's **partition pruning**, the whole point: a query scoped to
one partition's range does ~1/N of the I/O, with no index on `ts` needed.
Pruning is on by default (`enable_partition_pruning`) and works when the
predicate resolves before execution — keep partition-key predicates
simple and direct.

## 5. Run it

```bash
make test lessons/16_partitioning
```

Building and backfilling `events_part` (~3,000,000 rows) takes a few
seconds — that's expected.

## 6. The gate

Not speed-graded — it's about a structural property. The test runs
`expected.sql` (the November count on the original `events`) and
`indexes.sql`, checks your `solution.sql`'s rows match, then `EXPLAIN`s
it and counts scan nodes whose relation name starts with `events_p_`.
That count must be exactly **1** — proving pruning happened, not just
that the total matched.

## 7. The teaching point

Partitioning turns "scan everything, then filter" into "prove most of the
data is irrelevant before touching it." It fits time-series data: new
partitions are created as months arrive, and old ones dropped
(`DROP TABLE events_p_2023_10` — instant, with no bulk-delete dead
tuples; see lesson 15) once a retention window passes. The cost is
complexity: bounds must be maintained (often a scheduled job), and
cross-partition queries don't benefit from pruning.
