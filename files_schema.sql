-- files_schema.sql

-- Schema for files table
DROP TABLE IF EXISTS files;

CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user TEXT,
    group_name TEXT,
    department TEXT NOT NULL,
    project TEXT,
    source TEXT NOT NULL,
    user_id TEXT,
    message_id TEXT,
    channel_id TEXT
);