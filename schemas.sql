-- schemas.sql

-- Schema for users table
DROP TABLE IF EXISTS users;

CREATE TABLE users (

)


-- Schema for files table
DROP TABLE IF EXISTS files;

CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user TEXT NOT NULL,
    department TEXT NOT NULL, -- mandatory
    project TEXT, -- optional
)