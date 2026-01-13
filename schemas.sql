-- schemas.sql

-- Schema for users table
DROP TABLE IF EXISTS users;

CREATE TABLE users (

)


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
    project TEXT, -- optional
)