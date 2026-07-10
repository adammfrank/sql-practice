# 04 — Assets & INNER JOIN

Each engagement involves testers enumerating hosts on the client's
network. Add an `assets` table: a host discovered during a specific
engagement, with a hostname (or IP), an OS guess, and the date it was
first seen.

## Task

- Design and create `assets`, tied to `engagements`.
- Seed a handful of assets across a few different engagements (some
  engagements get several assets, one gets zero — you'll need that for
  problem 5).
- Write a query returning, for every asset, its hostname alongside the
  name of the client it belongs to and the engagement's status — this
  requires going through two joins, not one.
- Write a second query: for each engagement, how many assets were
  discovered? Engagements with zero assets should *not* need to appear
  yet (that distinction is the point of the next problem).

## Think about

Why does going from "asset → engagement → client" require two separate
`JOIN` clauses instead of one? What's actually being matched in each?
