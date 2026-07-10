# Answer notes — 06

```sql
-- 1
SELECT e.id, f.severity, COUNT(*)
FROM engagements e
JOIN assets a ON a.engagement_id = e.id
JOIN findings f ON f.asset_id = a.id
GROUP BY e.id, f.severity;

-- 2
SELECT e.id, COUNT(*) AS critical_count
FROM engagements e
JOIN assets a ON a.engagement_id = e.id
JOIN findings f ON f.asset_id = a.id AND f.severity = 'critical'
GROUP BY e.id
HAVING COUNT(*) >= 3;

-- 3
SELECT c.name,
  (SELECT f.severity
   FROM findings f
   JOIN assets a ON a.id = f.asset_id
   JOIN engagements e ON e.id = a.engagement_id
   WHERE e.client_id = c.id
   ORDER BY CASE f.severity
     WHEN 'critical' THEN 4 WHEN 'high' THEN 3
     WHEN 'medium' THEN 2 ELSE 1 END DESC
   LIMIT 1) AS worst_finding
FROM clients c;

-- 4
SELECT c.name, COUNT(*) AS open_count
FROM clients c
JOIN engagements e ON e.client_id = c.id
JOIN assets a ON a.engagement_id = e.id
JOIN findings f ON f.asset_id = a.id AND f.status = 'open'
GROUP BY c.name
ORDER BY open_count DESC
LIMIT 1;
```

#3's `CASE` expression is the general technique for imposing a custom sort
order on a text enum that doesn't sort correctly alphabetically
(`critical` < `high` alphabetically, but shouldn't rank lower).
