-- user_schema.sql

-- Schema for users table
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    user_password TEXT NOT NULL,
    user_role TEXT NOT NULL,
    department TEXT,
    email TEXT,
    phone_number TEXT
);

-- Test data insertions
INSERT INTO users (username, user_password, user_role, department, email, phone_number) VALUES
-- Admin user
('admin', 'adminpass', 'admin', NULL, 'admin@example.com', '12345678'),
-- Standard user
('user', 'userpass', 'user', 'sales', 'user@example.com', '87654321');