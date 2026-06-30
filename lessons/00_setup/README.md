# Lesson 00 — Setup & Profiling Vocabulary

Welcome to SQL Performance Dojo. This lesson doesn't teach you a new SQL
technique yet — it teaches you the *tooling* you'll use for every lesson
after this one: how to run the harness, and how to read a Postgres
`EXPLAIN` plan.

There's nothing to fix here. `solution.sql` already has the correct query
in it. Your job is just to run the test, then actually read the plan it
produces, so the vocabulary ("Seq Scan", "Gather", "Aggregate", "Buffers")
is familiar before later lessons start asking you to make those plans
faster.

## 0. Prerequisites

If you haven't already:

```bash
docker compose up -d        # starts Postgres in a container
python -m dojo.seed         # builds and seeds the dojo_template database
```

`dojo.seed` creates `dojo_template` with ~5.5M rows spread across
`customers`, `products`, `orders`, `order_items`, `reviews`, and `events`.
Every lesson test clones that template into a fresh, throwaway database
before running, so nothing you do in one lesson leaks into another, and
there are never any indexes lying around except the ones you add
yourself in `indexes.sql`.

## 1. The problem

`expected.sql` (and, for this lesson only, `solution.sql` too) contains:

```sql
SELECT count(*) FROM orders WHERE status = 'pending';
```

`orders` has 500,000 rows; about 1 in 6 has `status = 'pending'`. There is
no index on `status` in the fresh lesson database, so Postgres has no
choice but to look at every row in the table to answer this query. That's
exactly the baseline behavior this lesson wants you to see.

## 2. Run it

```bash
.venv/Scripts/pytest lessons/00_setup -v
```

It should pass immediately — `solution.sql` is pre-filled with the
correct query, so there's nothing for you to edit. (Later lessons ship
`solution.sql` as a stub that fails until you fill it in correctly.)

## 3. Read the plan

The gate in `test_lesson.py` does two things:

1. **Correctness** — runs both `expected.sql` and `solution.sql` and
   checks the rows match (`grader.assert_rows_equal`).
2. **Plan shape** — runs `solution.sql` through
   `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` and asserts the plan contains
   a **Seq Scan** node (`grader.assert_plan(p, must_have=["Seq Scan"])`).
   There is **no speed assertion** in this lesson — we only care that you
   can see and name a full scan.

You can reproduce the same plan yourself from `psql` or any client
connected to a clone of `dojo_template`:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT count(*) FROM orders WHERE status = 'pending';
```

What each `EXPLAIN` option buys you:

- **`ANALYZE`** — actually *runs* the query (instead of just estimating)
  so the plan reports real timings and real row counts, not just the
  planner's guesses. (Caution in general: `ANALYZE` executes the query,
  including any side effects for `INSERT`/`UPDATE`/`DELETE` — irrelevant
  here since this is a `SELECT`.)
- **`BUFFERS`** — reports how many 8KB pages were read from shared
  buffers (cache hit) vs. read from disk, per node. This is usually a
  better "did this get cheaper" signal than wall-clock time alone,
  because it's stable across runs.
- **`FORMAT JSON`** — makes the output machine-parseable. The harness's
  `dojo.plan.Plan` class parses this JSON so the grader can walk the plan
  tree and assert on node types (`Plan.node_types()`, `Plan.has_node(...)`)
  instead of scraping text.

On this seeded dataset, the query above plans as something like:

```
Aggregate -> Gather -> Aggregate -> Seq Scan
```

Reading it inside-out: Postgres splits the table scan across parallel
workers (**Gather** collects their results), each worker does a
**Seq Scan** over its slice of `orders` re-checking the `status = 'pending'`
filter row by row, each worker partially aggregates its own count
(**Aggregate**), and the leader combines the partial counts into the
final one (**Aggregate**). You might also see a plain, non-parallel
`Seq Scan` directly under a single `Aggregate` if your machine's
Postgres decides parallelism isn't worth it for this table size — both
are "scan everything" plans, which is the point of this lesson.

**Seq Scan** means "read every row in the table (or this worker's slice
of it) and test the filter row by row." It's not inherently bad — for a
query that needs to touch most of the table anyway, it's often the
*fastest* available plan. But for a *selective* filter (one that matches
a small fraction of rows), a Seq Scan means Postgres is doing far more
I/O than necessary, which is the exact problem the next several lessons
will teach you to fix with indexes.

## 4. What's next

Lesson 01 starts asking you to actually write/improve queries and add
indexes. This lesson was just about making sure your environment works
and that `Seq Scan`, `Gather`, `Aggregate`, and `Buffers` are words you
recognize.
