# Interview Prep — General SQL & Schema Design

Prep track for a Data Domain / Raw SQL interview (CoderPad + Postgres, ~60
min, no ORM). Unlike `lessons/`, this isn't about indexing — it's schema
design, joins, normalization, subqueries, graph traversal, and
plain-English-to-SQL translation, in a single running scenario you build up
yourself.

There is no autograder here. You design the schema, so there's no single
"expected" answer to diff against. Work the problems in order — each one
assumes the tables from the ones before it exist. Answers live in
`answers/`, one file per problem — don't open one until you've written and
run your own attempt.

## Setup

Use the same Postgres container as the rest of the repo, but a throwaway
database so you don't collide with `dojo_template`:

```bash
make up   # if not already running
createdb -h 127.0.0.1 -U dojo -p ${POSTGRES_PORT:-5432} interview_prep
psql -h 127.0.0.1 -U dojo -p ${POSTGRES_PORT:-5432} interview_prep
```

(password is `dojo`, or set `PGPASSWORD=dojo` to skip the prompt)

Drop and recreate it any time you want a clean slate:

```bash
dropdb -h 127.0.0.1 -U dojo interview_prep && createdb -h 127.0.0.1 -U dojo interview_prep
```

## The scenario

You're building the schema behind an offensive-security engagement
tracker: clients hire the firm for pentest engagements, testers enumerate
assets (hosts) on the client's network, findings (vulnerabilities) get
logged against those assets, and hosts can reach each other over the
network — which matters once you get to lateral-movement path queries.

## Problems

1. `01_schema_design_core.md` — clients & engagements, normalization basics
2. `02_dml_practice.md` — seed data, constraints
3. `03_basic_queries.md` — SELECT / WHERE / ORDER BY / LIMIT
4. `04_joins_inner.md` — assets, INNER JOIN
5. `05_joins_left_and_findings.md` — findings, LEFT JOIN / anti-join
6. `06_aggregation.md` — GROUP BY / HAVING
7. `07_subqueries.md` — correlated subqueries, EXISTS
8. `08_many_to_many.md` — testers, junction tables
9. `09_graph_one_hop.md` — network reachability, self-joins
10. `10_graph_recursive.md` — recursive CTEs, multi-hop traversal
11. `11_window_functions.md` — ROW_NUMBER / RANK / PARTITION BY
12. `12_normalization_critique.md` — spot and fix a denormalized table
13. `13_efficiency_reasoning.md` — reasoning about indexes without writing one
14. `14_capstone.md` — one query, everything above

## How to work each one

Plain-English prompt, then a task list. No copy-paste DDL or query
skeletons — that's the point. If you get stuck, re-read the prompt for the
noun/verb pairs (e.g. "for each engagement" → `GROUP BY`, "that have never
had" → anti-join) before peeking at the answer.
