# 12 — Spot the Smell

Imagine you inherited this single table instead of the schema you've been
building:

> `finding_reports(report_id, client_name, client_contact_email,
> engagement_status, asset_hostname, asset_os, finding_title,
> finding_severity, cve_id, tester_name, tester_role)`

One row per finding. No other tables.

## Task

- List, in your own words, at least three concrete problems this design
  causes (think about what happens on: updating a client's contact email,
  deleting the last finding for an asset, inserting a newly discovered
  asset that has no findings yet). Name which normal form each problem
  violates if you can.
- Without writing full DDL, sketch (as prose, not SQL — table names and
  the columns that move into each) how you'd split this back into the
  normalized shape from problems 1, 4, 5, and 8.
- Given only this flat table already loaded with data, write the `INSERT
  ... SELECT DISTINCT` (or equivalent) you'd use to backfill just the
  `clients` table from it — this is the part that actually requires SQL.
