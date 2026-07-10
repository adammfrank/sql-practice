# Answer notes — 01

A billing contact reused across clients is many-to-many in the general
case (this contractor scenario), so don't embed contact fields on
`clients` — that's what causes the duplication/update-anomaly problem the
prompt is pointing at (updating one contact's phone number would require
finding and editing it on every client row that copied it). Reference
shape:

```sql
CREATE TABLE contacts (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT
);

CREATE TABLE clients (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  contact_id INTEGER NOT NULL REFERENCES contacts(id)
);

CREATE TABLE engagements (
  id SERIAL PRIMARY KEY,
  client_id INTEGER NOT NULL REFERENCES clients(id),
  status TEXT NOT NULL CHECK (status IN ('scoping','active','reporting','closed')),
  start_date DATE NOT NULL,
  end_date DATE,
  CHECK (end_date IS NULL OR end_date >= start_date)
);
```

This models client→contact as many-to-one (each client has one *current*
billing contact, but a contact can back multiple clients) — a `contact_id`
FK on `clients` is enough; you don't need a junction table unless a client
can have *multiple simultaneous* contacts, which the prompt didn't ask
for. Surrogate `SERIAL` id for contacts, not email, since email can change
for the same real person — a natural key you can't guarantee is stable
long-term is a bad primary key.
