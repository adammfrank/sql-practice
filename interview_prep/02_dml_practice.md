# 02 — Seed Data

Populate the tables from problem 1 by hand:

- 3 contacts (make one of them shared by two clients).
- 4 clients, using those contacts.
- 6 engagements spread across the 4 clients, covering every status value
  at least once, with realistic start/end dates (some engagements still
  open — no end date yet).

## Task

- Write the `INSERT` statements.
- Deliberately try one insert that should be *rejected* by a constraint
  you added in problem 1 (e.g. a bad status value, or a client with no
  contact if you made that required). Confirm Postgres rejects it, then
  fix it and re-run.
- Add one more engagement using a client lookup by name in a subquery
  rather than a hardcoded client id — i.e. the `INSERT` shouldn't require
  you to already know the client's numeric id.


INSERT INTO contacts (name, email, phone_number) values 
  ('George', 'g.eorge@gmail.com', '1234567890'),
  ('Jerry', 'j.errry@gmail.com', '1234567890'),
  ('Elaine', 'e.laine@gmail.com', '1234567890')


INSERT INTO clients (contact_id, name) VALUES 
(2, 'Acme'),
(2, 'Geico'),
(3, 'Sacred Heart'),
(4, 'Circa')

INSERT INTO engagements (client_id, start_date, end_date, status) VALUES
(1, '2026-07-08', '2027-07-09, 'active'),
(2, '2026-07-23', NULL, 'scoping'),
(3, '2026-09-23', NULL, 'reporting'),
(4, '2026-09-28', '2027-09-03', 'closed')
(1, '2026-07-08', '2027-08-03, 'active'),
(2, '2026-07-08', '2026-08-03, 'closed')

INSERT INTO engagements (client_id, start_date, end_date, status) VALUES
(1, '2026-07-08', '2027-07-09, 'blah')

 
INSERT INTO engagements (client_id, start_date, end_date, status) VALUES
(SELECT client_id, '2026-09-28', '2027-09-03', 'closed' FROM clients where name = 'Acme')
