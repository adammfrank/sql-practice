# Answer notes — 04

```sql
CREATE TABLE assets (
  id SERIAL PRIMARY KEY,
  engagement_id INTEGER NOT NULL REFERENCES engagements(id),
  hostname TEXT NOT NULL,
  os_guess TEXT,
  first_seen DATE NOT NULL DEFAULT CURRENT_DATE
);
```

```sql
SELECT a.hostname, c.name AS client, e.status
FROM assets a
JOIN engagements e ON e.id = a.engagement_id
JOIN clients c ON c.id = e.client_id;
```

```sql
SELECT e.id, COUNT(a.id)
FROM engagements e
JOIN assets a ON a.engagement_id = e.id
GROUP BY e.id;
```

Two joins because each `JOIN` matches on a *different* FK relationship —
`assets.engagement_id → engagements.id`, then separately
`engagements.client_id → clients.id`. There's no direct FK from assets to
clients, so there's no way to collapse this into one join condition; each
hop in the relationship chain needs its own join.

Note the second query silently drops engagements with 0 assets — that's
an `INNER JOIN` behavior, not a bug, and it's exactly the gap problem 5
fixes.
