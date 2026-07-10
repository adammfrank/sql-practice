# Answer notes — 08

Role is per tester-per-engagement, so it lives on the junction table, not
on `testers` or `engagements`:

```sql
CREATE TABLE testers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE engagement_testers (
  engagement_id INTEGER NOT NULL REFERENCES engagements(id),
  tester_id INTEGER NOT NULL REFERENCES testers(id),
  role TEXT NOT NULL CHECK (role IN ('lead','support')),
  PRIMARY KEY (engagement_id, tester_id)
);
```

Lead per engagement:

```sql
SELECT e.id, t.name
FROM engagements e
JOIN engagement_testers et ON et.engagement_id = e.id AND et.role = 'lead'
JOIN testers t ON t.id = et.tester_id;
```

Testers never a lead:

```sql
SELECT t.*
FROM testers t
WHERE NOT EXISTS (
  SELECT 1 FROM engagement_testers et
  WHERE et.tester_id = t.id AND et.role = 'lead'
);
```

The composite `PRIMARY KEY (engagement_id, tester_id)` also enforces "one
row per tester per engagement" for free — a tester can't accidentally get
assigned to the same engagement twice with two different roles.
