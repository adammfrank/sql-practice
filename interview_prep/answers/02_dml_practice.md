# Answer notes — 02

```sql
INSERT INTO contacts (name, email, phone) VALUES
  ('Pat Nguyen', 'pat@acme.com', '555-0101'),
  ('Jo Rivera',  'jo@shared.io', '555-0102'),
  ('Sam Okafor', 'sam@globex.com', '555-0103');

INSERT INTO clients (name, contact_id) VALUES
  ('Acme Corp', 1),
  ('Globex',    3),
  ('Initech',   2),
  ('Umbrella',  2);   -- Jo Rivera backs two clients

INSERT INTO engagements (client_id, status, start_date, end_date) VALUES
  (1, 'closed',    '2025-01-10', '2025-02-01'),
  (1, 'active',    '2026-06-01', NULL),
  (2, 'scoping',   '2026-07-01', NULL),
  (3, 'reporting', '2026-05-01', '2026-06-15'),
  (3, 'closed',    '2025-11-01', '2025-12-01'),
  (4, 'active',    '2026-06-20', NULL);
```

Constraint-violation check: try inserting `status = 'wontfix'` and confirm
the `CHECK` from problem 1 rejects it before fixing it to a real value.

Lookup-by-name insert:

```sql
INSERT INTO engagements (client_id, status, start_date)
SELECT id, 'scoping', '2026-07-05'
FROM clients WHERE name = 'Acme Corp';
```
