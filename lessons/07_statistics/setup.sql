-- Lesson 07 scenario setup: a "day-2 order surge."
--
-- Insert 200,000 new orders, all status = 'pending', with ids above the
-- current max — and deliberately do NOT run ANALYZE afterward. That leaves
-- the planner's cached statistics (from the template's seed-time ANALYZE)
-- out of date: it still thinks 'pending' is ~1-in-6 of the table.
--
-- This is the exact state the lesson's test creates in its throwaway clone;
-- `make lab lessons/07_statistics` applies it here so you can inspect it by
-- hand. It runs once, before you start experimenting.
INSERT INTO orders (id, customer_id, status, total, created_at)
SELECT gs, (gs % 50000) + 1, 'pending', 42.00, now()
FROM generate_series(
    (SELECT max(id) FROM orders) + 1,
    (SELECT max(id) FROM orders) + 200000
) AS gs;
