# 11 — Window Functions

## Task

1. For each asset, rank its findings from most to least severe (critical
   first), without collapsing rows the way `GROUP BY` would — every
   finding should still appear, just with a rank column attached.
2. For each engagement, return only the single most recently discovered
   finding (by discovery date) — one row per engagement. Do it with a
   window function, not `LIMIT` (which can't easily do "top 1 per
   group").
3. For each client, compute a running total of engagement count over
   time, ordered by engagement start date (engagement 1 → running total
   1, engagement 2 → running total 2, etc., per client).
4. Explain the difference between `RANK()`, `DENSE_RANK()`, and
   `ROW_NUMBER()` using a concrete tie in your findings data (two findings
   with the same severity) — what does each one produce for that tie?
