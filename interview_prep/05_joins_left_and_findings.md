# 05 — Findings & LEFT JOIN

Add a `findings` table: a vulnerability logged against a specific asset,
with a title, a severity (`low`, `medium`, `high`, `critical`), a CVE
identifier (optional — not every finding maps to a CVE), and a status
(`open`, `remediated`).

## Task

- Design and create `findings`, tied to `assets`.
- Seed findings so that at least one asset has multiple findings, and at
  least one asset has none.
- Write a query listing every asset and its finding count, including
  assets with zero findings (they should show `0`, not disappear from the
  results).
- Write a second query returning only the assets with *zero* findings —
  an "asset never got tested" report. Don't use a subquery with `COUNT`
  for this one; there's a join-shaped way to express "rows on the left
  with no match on the right."
- Explain in one line: what's the difference between putting a filter on
  `findings.severity` in the `ON` clause of your `LEFT JOIN` versus in the
  `WHERE` clause? (Try both and compare the row counts if you're not
  sure.)
