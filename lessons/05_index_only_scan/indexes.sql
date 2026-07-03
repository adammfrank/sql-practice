-- Add a covering index: one that includes every column this query
-- needs, so Postgres never has to visit the table heap at all.
-- See README.md for the INCLUDE syntax and why VACUUM matters here.
create index idx_orders_customer_id on orders (customer_id) include (total)