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
    user TEXT, -- user who uploaded the file (optional, from Discord or web)
    group_name TEXT, -- optional (Discord channel name, only for Discord)
    department TEXT NOT NULL, -- mandatory (takes from user table for web uploads and role from discord uploads)
    project TEXT, -- optional
    source TEXT NOT NULL, -- source of upload: 'discord' or 'web'
    user_id TEXT, -- optional (Discord user ID, only for Discord uploads)
    message_id TEXT, -- optional (Discord message ID, only for Discord uploads)
    channel_id TEXT -- optional (Discord channel ID, only for Discord uploads)
);



-- Test data insertions
INSERT INTO users (username, user_password, user_role, department) VALUES
('admin', 'adminpass', 'admin', NULL);