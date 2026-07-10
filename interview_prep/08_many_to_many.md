# 08 — Testers & Many-to-Many

The firm's testers aren't tied to a single engagement — several testers
can work one engagement, and one tester works many engagements over time
(and needs a role on each, e.g. `lead` or `support`, since the same person
might lead one engagement and support another).

## Task

- Design and create a `testers` table and whatever else is needed to
  represent "which testers worked which engagements, in what role" —
  think about where the *role* attribute has to live given it's specific
  to one tester/engagement pairing, not to the tester or the engagement
  alone.
- Seed 4 testers, and assign them to engagements so at least one
  engagement has 2+ testers and at least one tester has worked 2+
  engagements.
- Write a query: for each engagement, list the lead tester's name (there
  should be exactly one `lead` per engagement — don't enforce that with
  SQL yet, just query assuming it's true).
- Write a query: which testers have never been a `lead` on anything?
