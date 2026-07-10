# Answer notes — 09

```sql
CREATE TABLE reachability (
  source_asset_id INTEGER NOT NULL REFERENCES assets(id),
  target_asset_id INTEGER NOT NULL REFERENCES assets(id),
  PRIMARY KEY (source_asset_id, target_asset_id)
);
```

A composite PK of `(source, target)` is what prevents a duplicate edge
from being silently double-counted; a surrogate `SERIAL` id would let the
same edge get inserted twice with no constraint catching it, which would
quietly inflate any downstream hop-counting query.

One hop:

```sql
SELECT target_asset_id FROM reachability WHERE source_asset_id = :host;
```

Two hops, self-join, excluding the start:

```sql
SELECT DISTINCT r2.target_asset_id
FROM reachability r1
JOIN reachability r2 ON r2.source_asset_id = r1.target_asset_id
WHERE r1.source_asset_id = :host
  AND r2.target_asset_id != :host;
```

Past 2-3 hops, chaining more self-joins doesn't scale — you don't know the
max path length in advance, and each extra join is unwieldy to write and
gets more expensive. That's the motivation for problem 10's recursive CTE,
which handles "any number of hops" in one query.
