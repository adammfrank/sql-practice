-- Add the index that lets Postgres find a customer's orders without
-- scanning the whole `orders` table. See README.md for the goal.
CREATE index idx_orders_customer on orders (customer_id)