-- The live aggregate — same query as lesson 01, reused here as both the
-- correctness answer key AND the speed baseline the matview must beat.
SELECT p.category, SUM(oi.quantity * oi.price) AS revenue
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'paid'
GROUP BY p.category;
