-- Add an index that lets Postgres satisfy both the WHERE and the
-- ORDER BY ... LIMIT without a separate Sort step. See README.md.
CREATE INDEX idx_orders_customer_id_created_at on orders(customer_id, created_at desc)