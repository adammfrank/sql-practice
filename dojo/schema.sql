CREATE TABLE customers (
    id          bigint PRIMARY KEY,
    name        text NOT NULL,
    email       text NOT NULL,
    country     text NOT NULL,
    created_at  timestamptz NOT NULL
);

CREATE TABLE products (
    id          bigint PRIMARY KEY,
    name        text NOT NULL,
    category    text NOT NULL,
    price       numeric(10,2) NOT NULL,
    description text NOT NULL,
    attributes  jsonb NOT NULL
);

CREATE TABLE orders (
    id          bigint PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    status      text NOT NULL,
    total       numeric(12,2) NOT NULL,
    created_at  timestamptz NOT NULL
);

CREATE TABLE order_items (
    id          bigint PRIMARY KEY,
    order_id    bigint NOT NULL REFERENCES orders(id),
    product_id  bigint NOT NULL REFERENCES products(id),
    quantity    int NOT NULL,
    price       numeric(10,2) NOT NULL
);

CREATE TABLE reviews (
    id          bigint PRIMARY KEY,
    product_id  bigint NOT NULL REFERENCES products(id),
    rating      int NOT NULL,
    body        text NOT NULL,
    created_at  timestamptz NOT NULL
);

CREATE TABLE events (
    id          bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    event_type  text NOT NULL,
    payload     jsonb NOT NULL,
    ts          timestamptz NOT NULL
);
