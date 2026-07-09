# 06 — Aggregation

## Task

1. For each engagement, count findings by severity (one row per
   engagement/severity combo, with the count).
2. List only the engagements that have 3 or more `critical` findings —
   filtering on an aggregated value, not a raw column.
3. For each client, find their single highest-severity finding ever
   recorded across all their engagements (treat severity as ordered:
   critical > high > medium > low). This requires mapping the text
   severity to something sortable.
4. Which client has the most *open* findings right now, and how many?
   One query, one row of output.
