# 14 — Capstone

One query, using everything from problems 1–11 on the schema you've built.

## Task

Produce a single result set — one row per client — with:

- The client's name.
- Their total number of engagements.
- Their total number of `critical` findings across all engagements,
  counting zero for clients with none (not dropping them).
- The name of their most-recently-active engagement's `lead` tester (null
  if none).
- Only include clients that have had at least one engagement in the last
  two years.
- Order by critical-finding count, descending.

Write it as one query. If you reach for a CTE to keep it readable, that's
fine and often the better answer than one deeply nested query — say out
loud why you split it where you did.
