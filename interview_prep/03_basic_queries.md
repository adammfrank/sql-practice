# 03 — Basic Queries

Warm-up on the data from problems 1–2.

## Task

Write a separate query for each:

1. List every engagement that is currently `active`, most recently
   started first.
2. List clients whose name contains "Corp" (case-insensitive), regardless
   of how it's capitalized in the data.
3. Find the single engagement with the earliest start date. Do it two
   ways: once with `ORDER BY` + `LIMIT`, once without using `LIMIT` at
   all.
4. List engagements that have no end date yet, along with the client name
   they belong to.
5. Count how many distinct clients have ever had an engagement — not how
   many engagements exist.
