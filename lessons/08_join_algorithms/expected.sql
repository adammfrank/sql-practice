SELECT o.id, sum(oi.quantity * oi.price) AS total_items_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.customer_id = 4242
GROUP BY o.id;
