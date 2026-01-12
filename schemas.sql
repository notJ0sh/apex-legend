-- schemas.sql

-- Schema for users table
DROP TABLE IF EXISTS users;

CREATE TABLE users (

)


-- Schema for files table
DROP TABLE IF EXISTS files;

CREATE TABLE files (
    id,
    file_name,
    file_type,
    time_stamp,
    user,
    department,
    project,
)