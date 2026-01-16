-- user_schema.sql

-- Schema for users table
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    user_password TEXT NOT NULL,
    user_role TEXT NOT NULL,
    department TEXT
);

-- Test data insertions
INSERT INTO users (username, user_password, user_role, department) VALUES
('admin', 'adminpass', 'admin', NULL);