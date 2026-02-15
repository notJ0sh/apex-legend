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
('WDP slides', 'PPT', '/downloads/wdp_slides.ppt', 'reanne', 'team1', 'HR', 'WDP26', 'discord', 'user_001', 'msg_001', 'ch_001'),
-- file #2
('ADA report', 'WORD', '/downloads/ada_report.docx', 'maitri', 'team2', 'IT', 'ADA26', 'web', 'user_002', 'msg_002', 'ch_002'),
-- file #3
('USG docs', 'DOC', '/downloads/usg_docs.doc', 'joshua', 'team3', 'FINANCE', 'WDP26', 'discord', 'user_003', 'msg_003', 'ch_003'),
-- file #4
('SRM pdf', 'PDF', '/downloads/srm_pdf.pdf', 'travis', 'team4', 'LOGISTICS', 'ADA26', 'web', 'user_004', 'msg_004', 'ch_004'),
-- file #5
('PCS jpg', 'JPG', '/downloads/pcs_jpg.jpg', 'notjosh', 'team5', 'MARKETING', 'WDP26', 'discord', 'user_005', 'msg_005', 'ch_005'),
-- file #6
('DDA pdf', 'PDF', '/downloads/dda_pdf.pdf', 'notmaitri', 'team6', 'IT', 'ADA26', 'web', 'user_006', 'msg_006', 'ch_006');