# 07 — Subqueries

## Task

1. List engagements where every single finding (not just some) has been
   remediated — including engagements with zero findings at all. Do this
   with `NOT EXISTS`, not a `COUNT`/`HAVING` trick.
2. List engagements that have at least one `critical` finding still
   `open`, using `EXISTS` this time instead of a `JOIN`.
3. List clients whose total number of engagements is above the average
   number of engagements per client (a subquery that returns a single
   scalar, used in a `WHERE` comparison).
4. Rewrite #2 as a plain `INNER JOIN` instead of `EXISTS`, and note in a
   comment: for this data size it won't matter, but what could go wrong
   with the `JOIN` version if an engagement has *multiple* qualifying
   findings, and your `SELECT` list also asks for `engagements.*`?
