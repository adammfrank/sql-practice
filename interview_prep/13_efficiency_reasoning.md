# 13 — Efficiency Reasoning (No Index-Writing Required)

You won't have time in the interview to seed millions of rows and measure
anything — this is about reasoning out loud, the way `lessons/` had you
verify empirically.

## Task

For each scenario, say what you'd check or add, and why — a sentence or
two, no need to actually build million-row tables here:

1. `findings` has grown to 5 million rows. A dashboard runs `SELECT *
   FROM findings WHERE asset_id = ? AND status = 'open'` constantly. What
   index would you add, and does column order in a composite index matter
   for this particular query?
2. The same table also supports `SELECT * FROM findings WHERE severity =
   'critical'`, and 90% of all findings are `low` or `medium`. Is a
   plain index on `severity` obviously a good idea? What would make you
   check twice before adding it?
3. A report page runs `SELECT asset_id, COUNT(*) FROM findings WHERE
   status = 'open' GROUP BY asset_id`. Would an index on `status` alone
   let Postgres skip reading `findings` rows entirely, or only skip
   deciding *which* rows to read?
4. You're asked "why is this query slow" on unfamiliar Postgres SQL in
   the interview. What's the first command you run before guessing at a
   fix?
