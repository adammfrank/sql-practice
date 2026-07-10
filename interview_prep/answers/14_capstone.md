# Answer notes — 14

```sql
WITH latest_engagement AS (
  SELECT DISTINCT ON (e.client_id) e.client_id, e.id AS engagement_id
  FROM engagements e
  ORDER BY e.client_id, e.start_date DESC
),
crit_counts AS (
  SELECT c.id AS client_id, COUNT(f.id) AS critical_count
  FROM clients c
  LEFT JOIN engagements e ON e.client_id = c.id
  LEFT JOIN assets a ON a.engagement_id = e.id
  LEFT JOIN findings f ON f.asset_id = a.id AND f.severity = 'critical'
  GROUP BY c.id
)
SELECT
  c.name,
  COUNT(DISTINCT e.id) AS total_engagements,
  cc.critical_count,
  t.name AS lead_of_latest_engagement
FROM clients c
JOIN engagements e ON e.client_id = c.id
JOIN crit_counts cc ON cc.client_id = c.id
LEFT JOIN latest_engagement le ON le.client_id = c.id
LEFT JOIN engagement_testers et
  ON et.engagement_id = le.engagement_id AND et.role = 'lead'
LEFT JOIN testers t ON t.id = et.tester_id
GROUP BY c.name, cc.critical_count, t.name
HAVING MAX(e.start_date) >= CURRENT_DATE - INTERVAL '2 years'
ORDER BY cc.critical_count DESC;
```

Splitting rationale: `latest_engagement` needs `DISTINCT ON`, which can't
compose cleanly inside the same query as the aggregate joins without
either duplicating rows or fighting `GROUP BY` — pulling it into its own
CTE keeps "find one row per client" and "count/join everything else"
independent instead of tangled into one join graph. `crit_counts` is
separated for the same reason: computing it as a plain join alongside
`latest_engagement` would multiply finding rows by however many
engagements/testers matched, inflating `COUNT(f.id)`. Aggregating it to
one row per client *first*, then joining that single number in, avoids
the fan-out entirely — this is the general fix for "wrong count after
adding a join" bugs.
