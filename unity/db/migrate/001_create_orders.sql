-- Unity target schema
CREATE TABLE subscription_orders (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL,
  subscription_plan_id UUID NOT NULL,
  current_period_start TIMESTAMP NOT NULL,
  current_period_end TIMESTAMP NOT NULL,
  status TEXT CHECK (status IN ('active','cancelled','trialing','past_due')) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transactional_orders (
  id UUID PRIMARY KEY,
  customer_id UUID NULL,
  order_date TIMESTAMP NOT NULL,
  total_amount NUMERIC(10,2) NOT NULL
);

CREATE TABLE order_line_items (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL,
  order_type TEXT CHECK (order_type IN ('subscription','transactional')),
  product_id UUID NOT NULL,
  quantity INT,
  price NUMERIC(10,2)
);

CREATE TABLE hothx_products (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL,
  product_code TEXT NOT NULL,
  subscription_status TEXT CHECK (subscription_status IN ('provisional','active','cancelled')) NOT NULL,
  original_source_table TEXT NOT NULL,
  conversion_date TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
