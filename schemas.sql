-- schemas.sql

-- Schema for users table
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- unique identifier for each user
    username TEXT UNIQUE NOT NULL, -- unqiue username
    user_password TEXT NOT NULL, -- unique password
    user_role TEXT NOT NULL, -- admin or user
    department TEXT -- optional (only for users with role user)
);


-- Schema for files table
DROP TABLE IF EXISTS files;

CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- unique identifier for each file
    file_name TEXT NOT NULL, -- name of the file
    file_type TEXT NOT NULL, -- e.g., pdf, docx, png
    file_path TEXT NOT NULL, -- path where the file is stored
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- time of upload
    user TEXT NOT NULL, -- user who uploaded the file
    group_name TEXT, -- optional (only for discord)
    department TEXT NOT NULL, -- mandatory
    project TEXT -- optional
    description TEXT -- optional description of the file by gemini AI
);



-- Test data insertions
INSERT INTO users (username, user_password, user_role, department) VALUES
('admin', 'adminpass', 'admin', NULL);