# Answer notes — 12

Problems:
- Updating a client's contact email requires updating every finding row
  for that client — an update anomaly, and it's easy for rows to drift
  out of sync if you miss one. This is a 3NF violation:
  `client_contact_email` depends on `client_name`, not on the table's key
  (`report_id`) — a transitive dependency.
- Deleting the last finding for an asset deletes all record that the
  asset (and its OS) ever existed — a delete anomaly, since asset
  existence is only represented as a side effect of finding rows.
- Inserting a newly discovered asset with no findings yet is impossible
  without inventing a placeholder finding row — an insert anomaly, because
  the table has no way to represent an asset independent of a finding.

Redesign sketch: pull `client_name`/`client_contact_email` out into
`clients` (+ `contacts`), `engagement_status` into `engagements`,
`asset_hostname`/`asset_os` into `assets`, `tester_name`/`tester_role`
into `testers` + a junction table, leaving `finding_reports` reduced down
to just `finding_title`, `finding_severity`, `cve_id`, and a foreign key
to `asset_id` — i.e. exactly the schema from problems 1, 4, 5, 8.

Backfilling `clients`:

```sql
INSERT INTO clients (name, contact_id)
SELECT DISTINCT client_name, c.id
FROM finding_reports fr
JOIN contacts c ON c.email = fr.client_contact_email;
```
(assuming `contacts` gets backfilled first, from `DISTINCT
client_contact_email` rows in the flat table.)
