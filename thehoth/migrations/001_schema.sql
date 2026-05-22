-- Legacy thehoth schema
CREATE TABLE orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT NOT NULL,
  product_id INT NOT NULL,
  subscription_id INT NULL,
  type VARCHAR(32) DEFAULT 'one_time',
  has_recurring_items TINYINT DEFAULT 0,
  total DECIMAL(10,2),
  created_at DATETIME,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT,
  price DECIMAL(10,2),
  FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE subscriptions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT,
  plan_id INT,
  status ENUM('active','cancelled','trialing','past_due'),
  start_date DATETIME,
  end_date DATETIME,
  billing_frequency VARCHAR(16)
);

CREATE TABLE campaign_order (
  id INT PRIMARY KEY,
  order_id INT NOT NULL,
  campaign_id INT NOT NULL,
  attribution_date DATETIME
);

CREATE TABLE hothservices_orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT,
  product_id INT,
  product_code VARCHAR(64),
  status VARCHAR(32) DEFAULT 'provisional',
  created_at DATETIME
);

CREATE TABLE order_notes (
  id INT PRIMARY KEY,
  order_id INT,
  note TEXT
);

CREATE TABLE products (
  id INT PRIMARY KEY,
  name VARCHAR(255),
  hothx_flag TINYINT DEFAULT 0
);

CREATE TABLE invoices (
  id INT PRIMARY KEY,
  order_id INT,
  amount DECIMAL(10,2)
);

CREATE TABLE payments (
  id INT PRIMARY KEY,
  invoice_id INT,
  amount DECIMAL(10,2)
);
