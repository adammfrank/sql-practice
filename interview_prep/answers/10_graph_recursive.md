# Answer notes — 10

```sql
WITH RECURSIVE reach(asset_id, hops, path) AS (
  SELECT :host, 0, ARRAY[:host]
  UNION
  SELECT r.target_asset_id, reach.hops + 1, reach.path || r.target_asset_id
  FROM reach
  JOIN reachability r ON r.source_asset_id = reach.asset_id
  WHERE NOT r.target_asset_id = ANY(reach.path)
)
SELECT * FROM reach WHERE hops > 0;
```

Cycle safety comes from two things together: `UNION` (not `UNION ALL`)
dedupes identical `(asset_id, hops, path)` rows, but that alone doesn't
stop a cycle from producing ever-longer paths through the same nodes —
the real guard is `WHERE NOT r.target_asset_id = ANY(reach.path)`, which
refuses to revisit a node already in the current path, so the recursion
can't loop forever even with `A → B → A` in the data.

The termination mechanism generally: a recursive CTE stops when its
recursive term produces zero new rows in some iteration — Postgres
evaluates the recursive branch repeatedly against only the *previous*
iteration's new rows until it contributes nothing. The path-tracking
`WHERE` clause is what guarantees that "nothing new" state is actually
reached instead of the query spinning on a cycle.
