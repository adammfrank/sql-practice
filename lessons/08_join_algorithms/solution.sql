-- Part B: per-order item totals for one customer. Selecting o.id (not just
-- the sum) so each row identifies which order the total belongs to.
SELECT o.id, SUM(oi.quantity * oi.price) AS total_items_value
FROM orders AS o JOIN order_items AS oi ON o.id = oi.order_id
WHERE o.customer_id = 4242 GROUP BY o.id;