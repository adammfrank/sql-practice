-- Not used for row-correctness in this lesson (the gate compares planner
-- row-count estimates, not query results). Kept for convention/consistency
-- with the other lessons' probe query.
SELECT id FROM orders WHERE status = 'pending';
