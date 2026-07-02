# SQL Performance Dojo

A self-directed, pytest-graded course on SQL performance and indexing in
PostgreSQL. Each lesson gives you a slow query; you make it fast by adding
the right index (or DDL) and/or rewriting the query, and an automated gate
checks your work for correctness, query plan shape, and speed.

## Prerequisites

- Docker + Docker Compose
- Python 3.11+

## Setup

```bash
uv venv
uv pip install -e ".[dev]"
cp .env.example .env
make up          # or: docker compose up -d
make seed        # generates ~5.5M rows into dojo_template; takes ~1-2 min
```

`make seed` runs `python -m dojo.seed`, which builds the `dojo_template`
database (customers, products, orders, order_items, reviews, events) once.
Every lesson test clones that template into a fresh, throwaway database
before running, so nothing you do in one lesson — indexes, bloat, dropped
tables — leaks into another.

## The gameplay loop

Each lesson lives in `lessons/NN_<name>/`:

1. Read the lesson's `README.md` — the problem, the target plan shape, and
   the performance target.
2. Edit `indexes.sql` — add any `CREATE INDEX` / DDL the lesson calls for.
   This file is applied before your query runs.
3. Edit `solution.sql` — write the query.
4. Run the lesson's tests:

   ```bash
   uv run pytest lessons/NN_<name>
   ```

Note: running bare `pytest` (or `make test`) runs the **entire** suite,
including the harness's own unit tests and every lesson — use the
`lessons/NN_<name>` path to focus on the one you're working on.

## How grading works

Each lesson's gate checks three things, in order, with teaching-oriented
failure messages:

1. **Correctness** — your `solution.sql` and the lesson's reference query
   are run against the same database clone, and the result rows must
   match.
2. **Query plan** — your query is run through
   `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` and the gate asserts on the
   plan shape: the right node types are present (e.g. `Index Scan`) and
   the wrong ones are absent (e.g. no more `Seq Scan`), and/or that a
   specific index was used.
3. **Speed** — your query's execution time must beat a calibrated
   baseline by the lesson's target ratio (e.g. "at least 8x faster").

The baseline for each lesson is measured **on your own machine** the first
time you run it (best-of-N `EXPLAIN ANALYZE` timing of the naive/reference
query) and cached in `data/baseline.json`, so the speed target is fair
regardless of your hardware.

### Resetting your baseline

If your machine's performance characteristics change (new hardware, the
database got reseeded, etc.) and your cached baselines no longer make
sense, delete the cache and it will be recalibrated on the next run:

```bash
rm data/baseline.json
```

## The curriculum

**Part 0 — Profiling vocabulary**
- `00_setup` — run the harness, read your first `EXPLAIN` plan, learn Seq Scan/Gather/Aggregate/Buffers.

**Part 1 — First speedups**
- `01_select_filter` — WHERE/JOIN/GROUP BY refresher; correctness-only gate.
- `02_first_index` — add a single-column B-tree index to turn a Seq Scan into an Index Scan.

**Part 2 — Core B-tree indexing**
- `03_composite_index` — multi-column indexes; why column order matters.
- `04_left_prefix` — why `(a,b)` helps `WHERE a=` but not `WHERE b=` alone.
- `05_index_only_scan` — covering indexes (`INCLUDE`) and Index Only Scans.
- `06_order_by_index` — use an index to eliminate a Sort node.

**Part 3 — Planner & joins**
- `07_statistics` — `ANALYZE`, `pg_statistic`, selectivity, and how stale stats cause bad plans.
- `08_join_algorithms` — nested-loop vs. hash vs. merge join, and when the planner picks each.
- `09_bitmap_scans` — bitmap index scans and combining multiple indexes.

**Part 4 — The index zoo**
- `10_partial_index` — a small index over a filtered subset for a big win.
- `11_expression_index` — functional indexes (e.g. `lower(email)`).
- `12_gin_fulltext` — GIN + `tsvector` full-text search vs. `LIKE '%...%'`.
- `13_gin_jsonb` — GIN indexes on JSONB containment (`@>`) queries.
- `14_gist_brin` — GiST and BRIN indexes for the large time-ordered `events` table.

**Part 5 — Operational performance (the MVCC world)**
- `15_mvcc_vacuum_bloat` — dead tuples, table/index bloat, `VACUUM`, fillfactor, HOT updates.
- `16_partitioning` — declarative partitioning and partition pruning.
- `17_materialized_views` — materializing an expensive aggregate and `REFRESH`.

**Part 6 — Capstone**
- `18_capstone` — a slow multi-table report query; hit an aggressive target using everything above.

## Troubleshooting

- **Connection hangs for ~2 minutes on startup.** If `POSTGRES_HOST` is set
  to `localhost`, some systems (notably Windows and Docker Desktop) resolve
  it to the IPv6 address `::1` first, and the connection attempt times out
  before falling back to IPv4. Use `POSTGRES_HOST=127.0.0.1` in `.env`
  instead (this is already the default in `.env.example`).
- **`Template 'dojo_template' missing. Run: python -m dojo.seed`** — you
  haven't seeded yet, or you reseeded into a different database name than
  your `.env` expects. Run `make seed`.
