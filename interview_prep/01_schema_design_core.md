# 01 — Core Schema: Clients & Engagements

A pentest firm needs to track its clients and the engagements (projects)
run for them. One client can commission many engagements over time, each
with its own start date, end date, and status (`scoping`, `active`,
`reporting`, `closed`).

A client also has a billing contact: a name, email, and phone number. The
firm has noticed that the *same* contact sometimes appears across multiple
clients (a contractor who represents two companies), and wants that
handled cleanly rather than duplicating name/email/phone every time it's
reused.

## Task

- Design and create the tables for clients, engagements, and contacts.
- Decide where the client ↔ contact relationship lives, and defend it in
  a one-line comment: is a client's billing contact one-to-one,
  one-to-many, or many-to-many with contacts?
- Pick primary keys and the foreign keys that tie engagements to clients.
- Add a `NOT NULL` / `CHECK` constraint somewhere that reflects a real rule
  of this domain (e.g. an engagement's end date rule, or a closed set of
  status values).

## Think about

- What breaks if you just put `contact_name`, `contact_email`,
  `contact_phone` directly on the `clients` table, given the reuse case
  above?
- Would you use a natural key (like email) or a surrogate key
  (auto-incrementing id) for contacts? Why?


  CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(contact_id),
    name TEXT NOT NULL
  )

  CREATE TABLE contacts (
    contact_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone_number TEXT NOT NULL
  )

  CREATE TABLE engagements (
    engagement_id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(client_id),
    start_date DATE,
    end_date DATE,
    status TEXT CHECK (status IN ('scoping', 'active', 'reporting', 'closed'))
  )
