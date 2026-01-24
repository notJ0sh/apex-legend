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

-- Test data insertions
INSERT INTO files (file_name, file_type, file_path, user, group_name, department, project, source, user_id, message_id, channel_id) VALUES
-- file #1
('WDP slides', 'PPT', '/downloads/wdp_slides.ppt', 'reanne', 'team1', 'HR', 'WDP26', 'discord', '250726R', 'abc', 'web-dev-grp'),
-- file #2
('ADA slides', 'WORD', '/downloads/ada_slides.docx', 'valene', 'team2', 'IT', 'ADA26', 'web', '123456A', 'xyz', 'ada-grp');