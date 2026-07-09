# Answer notes — 11

```sql
-- 1
SELECT f.*,
  RANK() OVER (
    PARTITION BY f.asset_id
    ORDER BY CASE severity WHEN 'critical' THEN 4 WHEN 'high' THEN 3
      WHEN 'medium' THEN 2 ELSE 1 END DESC
  ) AS severity_rank
FROM findings f;

-- 2
SELECT * FROM (
  SELECT f.*, a.engagement_id,
    ROW_NUMBER() OVER (PARTITION BY a.engagement_id ORDER BY f.discovered_at DESC) rn
  FROM findings f JOIN assets a ON a.id = f.asset_id
) ranked WHERE rn = 1;

-- 3
SELECT client_id, id, start_date,
  COUNT(*) OVER (PARTITION BY client_id ORDER BY start_date) AS running_total
FROM engagements;
```

#4: on a tie, `ROW_NUMBER()` still assigns distinct sequential numbers
(1, 2) — arbitrary as to which tied row gets which, but never a tie in the
output. `RANK()` gives both tied rows the *same* rank (e.g. both get 2)
and then skips the next rank (the row after jumps to 4). `DENSE_RANK()`
also gives both tied rows the same rank (2) but does *not* skip — the next
row gets 3. Whether skipping matters depends on whether you need "how many
things outrank me" (`RANK`) or "how many distinct rank tiers exist"
(`DENSE_RANK`).
