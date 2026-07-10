# Answer notes — 07

```sql
-- 1
SELECT e.*
FROM engagements e
WHERE NOT EXISTS (
  SELECT 1 FROM assets a JOIN findings f ON f.asset_id = a.id
  WHERE a.engagement_id = e.id AND f.status = 'open'
);

-- 2
SELECT e.*
FROM engagements e
WHERE EXISTS (
  SELECT 1 FROM assets a JOIN findings f ON f.asset_id = a.id
  WHERE a.engagement_id = e.id AND f.severity = 'critical' AND f.status = 'open'
);

-- 3
SELECT c.*
FROM clients c
WHERE (SELECT COUNT(*) FROM engagements e WHERE e.client_id = c.id)
  > (SELECT AVG(cnt) FROM (
       SELECT COUNT(*) cnt FROM engagements GROUP BY client_id
     ) per_client);

-- 4
SELECT DISTINCT e.*
FROM engagements e
JOIN assets a ON a.engagement_id = e.id
JOIN findings f ON f.asset_id = a.id
WHERE f.severity = 'critical' AND f.status = 'open';
```

#4's risk: without `DISTINCT`, an engagement with two qualifying findings
comes back as two duplicate rows, because the join fans out one row per
matching `findings` row, not per engagement. `EXISTS` never has this
problem — it's a boolean membership test, so it can't multiply your outer
rows no matter how many findings match.
