-- This composite index already exists (it was the answer to the
-- previous lesson). It does NOT help the query in this lesson's
-- README -- see why, then add the index that actually does.
CREATE INDEX idx_orders_cust_status ON orders (customer_id, status);

CREATE index idx_orders_status on orders(status);
