-- Add indexes on both join-relevant lookup columns so the planner can
-- drive the join with a Nested Loop instead of a Hash Join. See
-- README.md Part B for why both indexes are needed.
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);