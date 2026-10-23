DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. users
CREATE TABLE users (
    user_id             TEXT PRIMARY KEY,
    registration_date   DATE NOT NULL,
    acquisition_channel TEXT NOT NULL,
    country             TEXT NOT NULL,
    device_type         TEXT NOT NULL
);

-- 2. products
CREATE TABLE products (
    product_id   TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    price        NUMERIC(10,2) NOT NULL CHECK (price > 0)
);

-- 3. orders
CREATE TABLE orders (
    order_id     TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users(user_id),
    order_date   TIMESTAMPTZ NOT NULL,
    order_status TEXT NOT NULL CHECK (order_status IN ('completed', 'cancelled', 'returned'))
);

-- 4. order_items
CREATE TABLE order_items (
    order_item_id TEXT PRIMARY KEY,
    order_id      TEXT NOT NULL REFERENCES orders(order_id),
    product_id    TEXT NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    UNIQUE (order_id, product_id)  -- товар в заказе встречается не более одного раза
);

-- 5. events
CREATE TABLE events (
    event_id        TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(user_id),
    event_timestamp TIMESTAMPTZ NOT NULL,
    event_type      TEXT NOT NULL CHECK (event_type IN ('view', 'add_to_cart', 'checkout', 'purchase')),
    product_id      TEXT REFERENCES products(product_id),  -- nullable
    session_id      TEXT NOT NULL,
    order_id        TEXT REFERENCES orders(order_id)        -- nullable
);

-- Индексы для типичных JOIN'ов и фильтров
CREATE INDEX idx_orders_user_id        ON orders(user_id);
CREATE INDEX idx_orders_order_date     ON orders(order_date);
CREATE INDEX idx_order_items_order_id  ON order_items(order_id);
CREATE INDEX idx_order_items_product   ON order_items(product_id);
CREATE INDEX idx_events_user_id        ON events(user_id);
CREATE INDEX idx_events_timestamp      ON events(event_timestamp);
CREATE INDEX idx_events_order_id       ON events(order_id);
CREATE INDEX idx_events_product_id     ON events(product_id);