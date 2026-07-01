SELECT id
FROM orders
WHERE status = 'pending'
  AND created_at >= '2023-09-15'::timestamptz;
