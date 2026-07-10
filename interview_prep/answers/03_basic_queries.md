# Answer notes — 03

1. `WHERE status = 'active' ORDER BY start_date DESC`
2. `WHERE name ILIKE '%corp%'` — `ILIKE` (or `lower(name) LIKE lower(...)`)
   for case-insensitivity; plain `LIKE` is case-sensitive in Postgres.
3. `ORDER BY start_date LIMIT 1`, versus
   `WHERE start_date = (SELECT MIN(start_date) FROM engagements)`. The
   second returns *all* ties if two engagements share the earliest date;
   the first arbitrarily picks one unless you add a tiebreaker.
4. `SELECT e.*, c.name FROM engagements e JOIN clients c ON c.id =
   e.client_id WHERE e.end_date IS NULL` — note `end_date = NULL` never
   matches anything; you need `IS NULL`.
5. `SELECT COUNT(DISTINCT client_id) FROM engagements` — plain `COUNT(*)`
   counts engagements, not clients.
