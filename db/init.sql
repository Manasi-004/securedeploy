CREATE TABLE products (id SERIAL PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, price NUMERIC(10,2) NOT NULL);
CREATE TABLE users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'customer');
CREATE TABLE cart_items (
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  qty INT NOT NULL CHECK (qty BETWEEN 1 AND 10),
  PRIMARY KEY (user_id, product_id));
CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id),
  total NUMERIC(10,2) NOT NULL, ts TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE security_events (id BIGSERIAL PRIMARY KEY, ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  event TEXT NOT NULL, src_ip TEXT, username TEXT, detail TEXT);

INSERT INTO products (name, description, price) VALUES
  ('Widget', 'A handy all-purpose widget for everyday tasks.', 9.99),
  ('Gadget', 'Compact smart gadget with a long-lasting battery.', 19.99),
  ('Gizmo', 'Tiny gizmo that fits in any pocket.', 4.50),
  ('Headphones', 'Wireless over-ear headphones with deep bass.', 59.00),
  ('Smart Watch', 'Track steps, sleep and notifications on your wrist.', 129.00),
  ('Backpack', 'Water-resistant backpack with a padded laptop sleeve.', 39.50),
  ('Keyboard', 'Quiet mechanical keyboard with backlit keys.', 49.99),
  ('Sunglasses', 'Polarized UV400 sunglasses for sunny days.', 24.00);
-- Lab users, unsalted MD5 ON PURPOSE.  alice / password123    bob / qwerty
INSERT INTO users (username, password_hash) VALUES
  ('alice', '482c811da5d5b4bc6d497ffa98491e38'),
  ('bob',   'd8578edf8458ce06fbc5bb76a58c5ca4');