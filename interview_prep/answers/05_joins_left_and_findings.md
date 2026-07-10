# Answer notes — 05

```sql
CREATE TABLE findings (
  id SERIAL PRIMARY KEY,
  asset_id INTEGER NOT NULL REFERENCES assets(id),
  title TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
  cve_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('open','remediated'))
);
```

Count including zeros:

```sql
SELECT a.id, a.hostname, COUNT(f.id) AS finding_count
FROM assets a
LEFT JOIN findings f ON f.asset_id = a.id
GROUP BY a.id, a.hostname;
```
`COUNT(f.id)` (not `COUNT(*)`) is what makes unmatched rows count as 0 —
`f.id` is NULL for the unmatched side, and `COUNT` ignores NULLs.

Anti-join (assets with zero findings):

```sql
SELECT a.*
FROM assets a
LEFT JOIN findings f ON f.asset_id = a.id
WHERE f.id IS NULL;
```

`ON`-clause filter vs `WHERE`-clause filter: putting `AND f.severity =
'critical'` in the `ON` clause still returns every asset (LEFT JOIN
semantics preserved — non-matching assets get a row with NULL finding
columns), it just restricts *which findings* qualify as a match. Putting
that same condition in `WHERE` instead throws away the NULL-side rows
entirely for assets with no critical finding, which silently turns your
LEFT JOIN into the equivalent of an INNER JOIN.
