# Lesson 16 — Declarative Partitioning and Partition Pruning

Indexes make lookups inside a table fast. **Partitioning** takes a
different approach for very large tables: instead of one giant table
with one giant index, you split the table itself into smaller physical
pieces ("partitions"), each holding a disjoint slice of the data — and
the planner can skip entire partitions it knows can't contain
matching rows.

## 1. The problem

`events` has 3,000,000 rows spanning roughly 2023-10-11 through
2023-11-14 — a little over a month of data. A query asking for just
one calendar month:

```sql
SELECT count(*) FROM events WHERE ts >= '2023-11-01' AND ts < '2023-12-01';
```

still has to consider the whole table, because `events` is one
physical relation. An index on `ts` would help (an Index Scan instead
of a Seq Scan), but the table still contains months of data mixed
together in the same heap, growing forever as more events arrive. In
many real systems, older partitions are also handled completely
differently from the current one — archived to cold storage, dropped
after a retention period, compressed — and it's awkward to do any of
that to *part* of a plain table.

## 2. Declarative partitioning

Postgres lets you declare a table as partitioned **by range** (there's
also list and hash partitioning) on one or more columns, then attach
child tables ("partitions") that each own a specific range of key
values:

```sql
CREATE TABLE events_part (
    id bigint NOT NULL,
    customer_id bigint,
    event_type text,
    payload jsonb,
    ts timestamptz NOT NULL
) PARTITION BY RANGE (ts);

CREATE TABLE events_p_2023_10 PARTITION OF events_part
    FOR VALUES FROM ('2023-10-01') TO ('2023-11-01');

CREATE TABLE events_p_2023_11 PARTITION OF events_part
    FOR VALUES FROM ('2023-11-01') TO ('2023-12-01');
```

`events_part` itself holds no rows directly — every row you insert
into it is routed, automatically, to whichever child partition's range
covers that row's `ts`. Each partition is a completely ordinary table
under the hood, with its own storage, and can even have its own
indexes.

Populate it from the original table:

```sql
INSERT INTO events_part SELECT * FROM events;
```

## 3. What to do

In `indexes.sql`, write the full DDL above: `CREATE TABLE events_part
... PARTITION BY RANGE (ts)`, two monthly partitions covering the
data's full range (2023-10 and 2023-11), and the `INSERT ... SELECT`
to populate it. (This is DDL/backfill, not a query — `indexes.sql`
runs once, before your `solution.sql`, exactly like every earlier
lesson's index-creation step; it's just heavier this time.)

In `solution.sql`, write the same one-month query as `expected.sql`,
but against your new partitioned table:

```sql
SELECT count(*) FROM events_part WHERE ts >= '2023-11-01' AND ts < '2023-12-01';
```

## 4. Partition pruning

Run `EXPLAIN` on that query and look at which partitions show up in
the plan:

```sql
EXPLAIN SELECT count(*) FROM events_part
WHERE ts >= '2023-11-01' AND ts < '2023-12-01';
```

Because the `WHERE` clause is a constant range that the planner can
compare directly against each partition's declared bounds, it proves
at planning time that `events_p_2023_10` cannot contain any matching
row — and leaves it out of the plan entirely. Only
`events_p_2023_11` is scanned. This is **partition pruning**, and it's
the entire point of partitioning a table this way: a query scoped to
one partition's range does roughly 1/N of the I/O of scanning the
whole (unpartitioned) table, for free, with no index needed on `ts` at
all (though you could add one per-partition for even faster access
within a partition).

Pruning is a planning-time optimization (`enable_partition_pruning`,
on by default) — it works whenever the predicate is a comparison
against a constant or a value known before execution starts. It's
lost if the predicate can't be resolved until execution (e.g. some
correlated subquery cases), so keep partition-key predicates simple
and direct.

## 5. Run it

```bash
.venv/Scripts/pytest lessons/16_partitioning -v
```

Building `events_part` and backfilling ~3,000,000 rows takes a few
seconds — that's expected for this lesson.

## 6. The gate

This lesson isn't ratio/speed-graded — it's DDL-heavy and about a
structural property (pruning), not a timing threshold. The test:

1. Runs `expected.sql` (the November count against the original,
   unpartitioned `events`) and `indexes.sql` (builds and backfills
   `events_part`).
2. Runs your `solution.sql` and checks its rows match `expected.sql`
   via `assert_rows_equal` — this fails immediately with the
   placeholder `SELECT 1;`, since `events_part` wouldn't even need to
   exist for that to run, and its single row obviously won't match the
   real count.
3. `EXPLAIN`s your `solution.sql` and walks the plan's nodes, counting
   scan nodes (`Seq Scan` / `Index Scan` / `Index Only Scan` /
   `Bitmap Heap Scan`) whose `Relation Name` starts with
   `events_p_` — i.e., how many partitions actually got scanned.
   Asserts that count is exactly **1**. If your query somehow forces a
   scan of both partitions (e.g. a non-constant or overly broad
   predicate), this assertion catches it even if the row count still
   happens to match.

## 7. The teaching point

Partitioning turns "scan everything, then filter" into "prove most of
the data is irrelevant before touching it." It pairs naturally with
time-series data like `events`: new partitions get created as new
months arrive, and old partitions can be dropped (`DROP TABLE
events_p_2023_10` — instant, since it's just removing a table, not a
row-by-row `DELETE`) once a retention window passes, without ever
touching an index or triggering a bulk-delete's worth of dead tuples
(see lesson 15). The tradeoff is complexity: partition bounds must be
maintained (often via a scheduled job that creates next month's
partition ahead of time), and cross-partition queries (spanning both
months) don't benefit from pruning — they still have to scan every
partition the predicate can't rule out.
