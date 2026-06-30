SELECT p.category, SUM(oi.quantity * oi.price) AS revenue
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'paid'
GROUP BY p.category;
