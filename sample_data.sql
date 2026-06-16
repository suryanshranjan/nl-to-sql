-- ============================================================================
-- sample_data.sql
-- ----------------------------------------------------------------------------
-- Creates the demo tables and inserts sample rows so you have something to
-- query right away.
--
-- Run it with psql:
--     psql -U postgres -d nl_to_sql_demo -f sample_data.sql
--
-- (Create the database first if needed:  CREATE DATABASE nl_to_sql_demo;)
-- ============================================================================

-- Start clean so the script can be re-run safely.
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

-- ----------------------------------------------------------------------------
-- customers: one row per customer
-- ----------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id   SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    city          VARCHAR(100) NOT NULL
);

-- ----------------------------------------------------------------------------
-- orders: one row per order, linked to a customer
-- ----------------------------------------------------------------------------
CREATE TABLE orders (
    order_id    SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount      NUMERIC(10, 2) NOT NULL,
    order_date  DATE NOT NULL
);

-- ----------------------------------------------------------------------------
-- Sample customers
-- ----------------------------------------------------------------------------
INSERT INTO customers (customer_name, city) VALUES
    ('Aarav Sharma',   'Mumbai'),
    ('Priya Patel',    'Ahmedabad'),
    ('Rohan Verma',    'Delhi'),
    ('Sneha Iyer',     'Mumbai'),
    ('Karan Mehta',    'Delhi'),
    ('Diya Nair',      'Bengaluru');

-- ----------------------------------------------------------------------------
-- Sample orders
-- A few of these use CURRENT_DATE so "orders placed this month" always works.
-- ----------------------------------------------------------------------------
INSERT INTO orders (customer_id, amount, order_date) VALUES
    (1, 1200.00, CURRENT_DATE),
    (1,  450.50, CURRENT_DATE - INTERVAL '2 days'),
    (2,  890.00, CURRENT_DATE - INTERVAL '40 days'),
    (3, 2300.75, CURRENT_DATE),
    (3,  150.00, CURRENT_DATE - INTERVAL '10 days'),
    (4, 3200.00, CURRENT_DATE - INTERVAL '5 days'),
    (4,  600.00, CURRENT_DATE - INTERVAL '65 days'),
    (5,  999.99, CURRENT_DATE - INTERVAL '1 day'),
    (5,  120.00, CURRENT_DATE - INTERVAL '90 days'),
    (6, 4500.00, CURRENT_DATE),
    (6,  250.25, CURRENT_DATE - INTERVAL '15 days'),
    (2, 1750.00, CURRENT_DATE - INTERVAL '3 days');
