# SQL Performance Dojo — Design

**Date:** 2026-06-30
**Status:** Approved for planning

## Purpose

A self-directed course for learning **SQL performance and profiling** through PostgreSQL.
The learner is comfortable with SQL basics (SELECT/JOIN/GROUP BY) and wants to focus on
query planning, indexing, and operational performance. Difficulty increases gradually.
Success on each lesson is *gated* by automated checks: a query must be correct, must use the
intended query plan, and must beat a calibrated performance target.

## Goals

- Teach how to read and reason about the PostgreSQL query planner (`EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`).
- Cover the full index zoo: B-tree (single, composite, covering/`INCLUDE`), partial, expression,
  GIN (full-text + JSONB), GiST, BRIN.
- Cover planner/statistics topics: `ANALYZE`, `pg_statistic`, selectivity, extended statistics,
  join algorithms (nested-loop / hash / merge), bitmap scans.
- Cover operational performance unique to MVCC engines: dead tuples, bloat, `VACUUM`, `fillfactor`,
  HOT updates, partitioning, materialized views.
- Require the learner to meet measurable performance targets to "pass" each lesson.

## Non-goals

- Not an ORM tutorial — all SQL is written by hand.
- Not a database administration course beyond the performance-relevant operational topics.
- Not portable to a single file: Postgres requires a running server (provisioned via Docker Compose).
  Portability was traded away deliberately in favor of teaching the real planner and the full
  feature set.

## Tech stack

- **Language/runtime:** Python 3.11+.
- **Test framework:** `pytest` — the grading harness and the gameplay loop.
- **DB driver:** `psycopg` v3 (raw SQL, no ORM).
- **Database:** PostgreSQL 16, provisioned via `docker-compose.yml` on a known port, data persisted
  in a named volume.
- **Data generation:** `faker` with a fixed random seed for deterministic, reproducible data so
  every learner's plans and timings are comparable.
- **Dependencies:** pinned in `pyproject.toml` (and a `requirements.txt` for convenience).

## Provisioning & isolation

- `docker compose up -d` starts Postgres. Connection settings live in `.env` (host, port, user,
  password, db) with sensible defaults.
- Data is seeded **once** into a template database `dojo_template` via `python -m dojo.seed`.
- Each lesson test **clones the template** (`CREATE DATABASE dojo_test_<lesson> TEMPLATE dojo_template`)
  to get a pristine, isolated database. This guarantees:
  - Indexes created in one lesson never leak into another.
  - Destructive experiments (bloat generation, `VACUUM`, partition creation) are sandboxed.
  - The template clone is a fast file-level copy, so per-lesson setup stays cheap.
- The test drops its clone on teardown.

## Dataset

Schema chosen to naturally exercise every index type. Approximate row counts (deterministic seed):

| Table         | Rows  | Notable columns / purpose                                              |
|---------------|-------|------------------------------------------------------------------------|
| `customers`   | ~50K  | name, email, country, created_at                                       |
| `products`    | ~10K  | name, price, category, `description text` (FTS), `attributes jsonb` (GIN) |
| `orders`      | ~500K | customer_id FK, status, total, created_at                              |
| `order_items` | ~1M   | order_id FK, product_id FK, qty, price                                  |
| `reviews`     | ~1M   | product_id FK, rating, `body text` (GIN full-text)                     |
| `events`      | ~3M   | user activity log, time-ordered append-only, `payload jsonb`, `ts` (BRIN, partitioning) |

Notes:
- `events` is intentionally large and naturally time-ordered to make BRIN and partition pruning meaningful.
- `products.attributes` (jsonb) and `reviews.body` (text) supply the GIN lessons.
- Foreign keys present to make join-algorithm lessons realistic.

## Gameplay loop

Each lesson is a numbered folder. The learner:
1. Reads `README.md` — problem statement, what the plan *should* look like, the performance target.
2. Writes any indexes/DDL in `indexes.sql` (applied before the solution runs).
3. Writes the query in `solution.sql`.
4. Runs `pytest lessons/NN_*`.

A lesson passes only when **all** of these hold, checked in order with teaching-oriented failure messages:
1. **Correctness** — result rows match the expected result set (`assert_rows_equal`).
2. **Plan** — the query plan matches the lesson's requirement (e.g. node type present/absent,
   specific index used) via `assert_plan` helpers.
3. **Performance** — execution time beats the calibrated target
   (`assert_faster_than_baseline`), expressed as a ratio against a per-machine baseline.

Failure messages print the actual `EXPLAIN` plan and the timing ratio so the learner sees *why* it failed.

## Performance gating & calibration

- Each lesson's test first measures a **baseline**: the reference query run without the helpful
  index/optimization, using PostgreSQL's reported **Execution Time** from `EXPLAIN ANALYZE`
  (more stable than wall-clock; excludes client/network), taken as best-of-N (e.g. best of 5) after a warm-up run.
- The target is expressed as a **ratio** (e.g. "your query must be ≥ 8× faster than baseline") plus
  a small **absolute floor** (e.g. ignore differences under a few ms) to avoid flakiness on trivially
  fast queries.
- The baseline is recorded in `data/baseline.json` so targets are meaningful on any hardware.
- Where appropriate, plan-based assertions (rows examined, buffer counts, node types) supplement
  timing so a pass requires the *right strategy*, not just luck.

## Curriculum (~18 lessons, increasing difficulty)

**Part 0 — Profiling vocabulary**
- `00_setup` — `docker compose up`, seed the template, learn `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`;
  read Seq Scan, cost vs. actual rows, buffers. Feel a full Seq Scan.

**Part 1 — First speedups**
- `01_select_filter` — WHERE/JOIN refresher; correctness-only gate to re-acclimate.
- `02_first_index` — single-column B-tree turns a Seq Scan into an Index Scan. First perf gate.

**Part 2 — Core B-tree indexing**
- `03_composite_index` — multi-column index; column order matters.
- `04_left_prefix` — why `(a,b)` helps `WHERE a=` but not `WHERE b=`.
- `05_index_only_scan` — covering indexes via `INCLUDE`; Index Only Scan; why the visibility
  map / `VACUUM` matters for index-only scans.
- `06_order_by_index` — use an index to eliminate the Sort node.

**Part 3 — Planner & joins**
- `07_statistics` — `ANALYZE`, `pg_statistic`, `n_distinct`, histograms, estimated-vs-actual rows,
  stale-stats bad plans, `CREATE STATISTICS` for correlated columns.
- `08_join_algorithms` — nested-loop vs hash vs merge join; when each is chosen; `work_mem`'s effect.
- `09_bitmap_scans` — bitmap index scans, combining multiple indexes (BitmapAnd / BitmapOr).

**Part 4 — The index zoo**
- `10_partial_index` — partial index (e.g. `WHERE status='pending'`); tiny index, big win.
- `11_expression_index` — functional index on `lower(email)` / date expressions.
- `12_gin_fulltext` — GIN + `tsvector` full-text search vs. `LIKE '%...%'`.
- `13_gin_jsonb` — GIN on JSONB / arrays; containment (`@>`) queries.
- `14_gist_brin` — GiST (ranges/KNN) and BRIN for the huge time-ordered `events` table.

**Part 5 — Operational performance (the MVCC world)**
- `15_mvcc_vacuum_bloat` — dead tuples, measure table/index bloat, `VACUUM`/autovacuum,
  `fillfactor`, HOT updates.
- `16_partitioning` — declarative partitioning + partition pruning.
- `17_materialized_views` — materialize an expensive aggregate; `REFRESH`.

**Part 6 — Capstone**
- `18_capstone` — a slow multi-table report query; hit an aggressive target using everything learned.

## Project layout

```
sql-practice/
  README.md                    # quickstart, how grading works
  pyproject.toml               # deps + tooling config
  requirements.txt             # convenience mirror of deps
  docker-compose.yml           # Postgres 16 service + volume
  .env.example                 # connection defaults
  Makefile                     # `make up`, `make seed`, `make test`, `make down` (optional convenience)
  dojo/                        # reusable harness package
    __init__.py
    config.py                  # read .env / connection settings
    db.py                      # psycopg connections; clone-from-template per lesson
    seed.py                    # deterministic data generation into dojo_template
    plan.py                    # run EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON); parse plan tree
    timing.py                  # baseline calibration + best-of-N measurement
    grader.py                  # assert_rows_equal, assert_plan, assert_faster_than_baseline
  data/
    baseline.json              # per-machine calibrated timings (gitignored)
  lessons/
    00_setup/
      README.md                # problem statement + expected plan shape + target
      indexes.sql              # learner writes CREATE INDEX / DDL here
      solution.sql             # learner writes the query here
      test_lesson.py           # provided; uses dojo.grader to gate correctness+plan+speed
    01_select_filter/ ...
    ...
    18_capstone/
  conftest.py                  # pytest fixtures: template DB, per-lesson clone, baseline
```

## Harness components (interfaces & responsibilities)

- **`dojo/config.py`** — loads connection params from `.env` with defaults. One responsibility:
  provide a connection string / params object.
- **`dojo/db.py`** — open psycopg connections; `clone_template(name)` and `drop_database(name)`
  helpers; context manager that yields a connection to a fresh per-lesson clone.
- **`dojo/seed.py`** — idempotent: drop/create `dojo_template`, create schema, generate deterministic
  data, `ANALYZE`. Runnable as `python -m dojo.seed`.
- **`dojo/plan.py`** — `explain(conn, sql) -> Plan`: runs `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`,
  returns a parsed tree with helpers: `find_nodes(type)`, `has_node(type)`, `uses_index(name)`,
  `execution_time_ms`, `total_buffers`.
- **`dojo/timing.py`** — `baseline(conn, sql)` (best-of-N execution time), `measure(conn, sql)`,
  and ratio comparison with absolute floor. Persists/reads `data/baseline.json`.
- **`dojo/grader.py`** — pytest-friendly assertions that compose the above and raise with the
  actual plan + timing on failure: `assert_rows_equal`, `assert_plan(plan, ...)`,
  `assert_faster_than_baseline(measured, baseline, ratio, floor_ms)`.
- **`conftest.py`** — fixtures: a session-scoped check that `dojo_template` exists (else instruct
  to run seed), a per-test clone fixture, and a baseline-loading fixture.

## Testing strategy

- The harness itself is the test runner for lessons.
- The harness code (`dojo/*`) gets its own unit tests (e.g. `tests/test_plan.py`,
  `tests/test_grader.py`) so plan parsing and grading logic are trustworthy — built test-first.
- A smoke test confirms `docker compose up` + seed + a trivial lesson pass works end to end.

## Error handling

- Missing/un-seeded template DB → clear message telling the learner to run `make seed`.
- Docker/Postgres not reachable → clear connection-error message pointing at `docker compose up`.
- Empty `solution.sql` → skipped/failing with a "write your query here" message.
- Plan parsing handles the documented `EXPLAIN ... FORMAT JSON` shape; unexpected shapes fail loudly.

## Open questions / deferred

- Exact per-lesson performance ratios and floors are tuned during implementation against the
  seeded dataset (each lesson author picks a target that is achievable with the intended solution
  and *not* achievable with the naive one).
- Optional `make` convenience targets vs. documenting raw commands — decide during implementation.
