-- Lesson 07 scenario setup: a "day-2 order surge."
--
-- Insert 200,000 new orders, all status = 'pending', with ids above the
-- current max — and deliberately do NOT run ANALYZE afterward. That leaves
-- the planner's cached statistics (from the template's seed-time ANALYZE)
-- out of date: it still thinks 'pending' is ~1-in-6 of the table.
--
-- First, switch off autovacuum for `orders` on this clone. Otherwise the
-- background autoanalyze daemon notices the ~40% churn and refreshes the
-- statistics on its own within a minute or so, silently "fixing" the very
-- staleness you came here to observe. (That auto-fix is exactly what happens
-- in production; the lab disables it only so the stale state holds still
-- until *you* run ANALYZE.)
--
-- This is the same state the lesson's test creates in its throwaway clone;
-- `make lab lessons/07_statistics` applies it here so you can inspect it by
-- hand. It runs once, before you start experimenting.
ALTER TABLE orders SET (autovacuum_enabled = false);

INSERT INTO orders (id, customer_id, status, total, created_at)
SELECT gs, (gs % 50000) + 1, 'pending', 42.00, now()
FROM generate_series(
    (SELECT max(id) FROM orders) + 1,
    (SELECT max(id) FROM orders) + 200000
) AS gs;
