#      -----      {{{     IMPORTS     }}}      -----      #

import sqlite3
import os
from datetime import datetime
from flask import g, Flask, Response, send_from_directory
from models import File
import requests

from log_handler import log_db_entry

#      -----      {{{     DATABASE CONSTANTS     }}}      -----      #

USER_DATABASE = 'user_data.db'
FILES_DATABASE = 'files_data.db'


#      -----      {{{     DIRECTORY CONSTANTS     }}}      -----      #

UPLOAD_DIRECTORY = 'downloads'


#      -----      {{{     DATABASE HELPERS     }}}      -----      #


# Get database connection for the current request context.
def get_database(db_name: str) -> sqlite3.Connection:
    """Get database connection for the current request context."""
    db_attr = f'_db_{db_name}'
    database = getattr(g, db_attr, None)

    if database is None:
        database = sqlite3.connect(db_name)
        database.row_factory = sqlite3.Row
        setattr(g, db_attr, database)

    return database


# Initialize database with schema from specified SQL file.
def init_database(db_name: str, schema_file: str, app: Flask) -> None:
    """Initialize database with schema from specified SQL file."""
    with app.app_context():
        database = get_database(db_name)
        with app.open_resource(schema_file) as f:
            sql_script = f.read().decode('utf-8')
            database.executescript(sql_script)
        database.commit()


# Scan downloads directory and add pre-existing files to database.
def scan_existing_downloads(app: Flask) -> None:
    """Scan downloads directory and add pre-existing files to database."""
    if not os.path.exists(UPLOAD_DIRECTORY):
        return
    
    with app.app_context():
        database = get_database(FILES_DATABASE)
        
        # Get all files already in the database
        cursor = database.execute('SELECT file_path FROM files')
        existing_paths = {row['file_path'] for row in cursor.fetchall()}
        
        # Scan the downloads directory
        for filename in os.listdir(UPLOAD_DIRECTORY):
            file_path = os.path.join(UPLOAD_DIRECTORY, filename)
            
            # Skip directories, only process files
            if not os.path.isfile(file_path):
                continue
            
            # Skip if already in database
            if file_path in existing_paths:
                continue
            
            # Extract file type from extension
            file_type = os.path.splitext(filename)[1].lstrip('.').upper()
            if not file_type:
                file_type = 'UNKNOWN'
            
            # Get file modification time
            mod_time = os.path.getmtime(file_path)
            time_stamp = datetime.fromtimestamp(mod_time).isoformat()
            
            # Prepare file data
            file_data = {
                'file_name': filename,
                'file_type': file_type,
                'file_path': file_path,
                'time_stamp': time_stamp,
                'user': 'admin123',
                'department': 'GENERAL',
                'project': 'GENERAL',
                'source': 'filesystem'
            }
            
            # Add to database
            try:
                columns = ', '.join(file_data.keys())
                placeholders = ', '.join('?' * len(file_data))
                sql = f'INSERT INTO files ({columns}) VALUES ({placeholders})'
                database.execute(sql, tuple(file_data.values()))
                print(f"✅ Added existing file to database: {filename}")
            except Exception as e:
                print(f"❌ Error adding existing file {filename}: {e}")
        
        database.commit()


# Ensure databases are created if they don't exist.
def ensure_databases(app: Flask) -> None:
    """Ensures databases are initialized at startup."""
    if not os.path.exists(USER_DATABASE):
        print(f"Creating {USER_DATABASE}...")
        init_database(USER_DATABASE, 'user_schema.sql', app)
        print(f"✅ {USER_DATABASE} created successfully")

    if not os.path.exists(FILES_DATABASE):
        print(f"Creating {FILES_DATABASE}...")
        init_database(FILES_DATABASE, 'files_schema.sql', app)
        print(f"✅ {FILES_DATABASE} created successfully")
        # Scan for existing files after database creation
        scan_existing_downloads(app)


# Close database connections at the end of request context.


def close_databases(error) -> None:
    """Close all database connections when the request context ends."""
    user_db = getattr(g, '_db_' + USER_DATABASE, None)
    if user_db is not None:
        user_db.close()

    files_db = getattr(g, '_db_' + FILES_DATABASE, None)
    if files_db is not None:
        files_db.close()


# Add data to specified table in the database.


def add_data(db_name: str, table: str, data: dict) -> None:
    """Add data to specified table in the database.

    Works with or without Flask application context.
    """
    try:
        # Try to use Flask's g object first (request context)
        database = get_database(db_name)
        should_close = False
    except RuntimeError:
        # Fallback for outside of Flask context (e.g., Discord bot thread)
        database = sqlite3.connect(db_name)
        database.row_factory = sqlite3.Row
        should_close = True

    try:
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        sql = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        database.execute(sql, tuple(data.values()))
        database.commit()
    finally:
        # Only close if we created the connection outside Flask context
        if should_close:
            database.close()

        # Log the information and success
        log_db_entry(data=data)


# Download file from URL to destination path.


def download_file(url: str, dest_path: str) -> bool:
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False
    except Exception as e:
        print(f"Error downloading file from {url}: {e}")
        return False

# Add data from Discord message to the database.


def add_data_from_discord(data: dict) -> None:
    # Define downloads folder
    downloads_folder = 'downloads'
    if not os.path.exists(downloads_folder):
        os.makedirs(downloads_folder)

    # Get the discord download link n data
    download_link = data.get("file_path")
    file_name = data.get("file_name")

    # Get local path
    local_path = os.path.join(downloads_folder, file_name)

    # Download the file + save the file metadata to the database along with the file path
    if download_file(download_link, local_path):
        # Update the file_path to local path before saving to DB
        data["file_path"] = local_path
        print(f"Downloaded file to {local_path}")

        # Save to database
        add_file_data(data)
    else:
        print(f"Failed to download file from {download_link}")


# Specific helper functions for user and file databases.


def add_user_data(data: dict) -> None:
    add_data(USER_DATABASE, 'users', data)


# Specific helper functions for user and file databases.


def add_file_data(data: dict) -> None:
    add_data(FILES_DATABASE, 'files', data)


# Retrieve user data by user ID.


def get_user_by_id(user_id: int) -> dict | None:
    """Retrieve user data by user ID."""
    try:
        # Try to use Flask's g object first (request context)
        database = get_database(USER_DATABASE)
        should_close = False
    except RuntimeError:
        # Fallback for outside of Flask context (e.g., Discord bot thread)
        database = sqlite3.connect(USER_DATABASE)
        database.row_factory = sqlite3.Row
        should_close = True

    try:
        sql = 'SELECT * FROM users WHERE id = ?'
        cursor = database.execute(sql, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        # Only close if we created the connection outside Flask context
        if should_close:
            database.close()


# Retrieve files by department
def get_files_by_department(department_name: str) -> list[File]:
    db = get_database(FILES_DATABASE)
    cursor = db.execute(
        'SELECT * FROM files WHERE department = ? ORDER BY time_stamp DESC',
        (department_name,)
    ).fetchall()

    return [File.from_row(row) for row in cursor]


# Check file exists by file name
def check_file_exists(filename: str) -> bool:
    return os.path.exists(os.path.join(UPLOAD_DIRECTORY, filename))


# Retrieve download file by file name and returns success status


def get_file_download(filename: str) -> Response:
    # Check if file exists
    if not check_file_exists(filename=filename):
        return Response("File not found.", status=404)

    return send_from_directory(
        UPLOAD_DIRECTORY,
        filename,
        as_attachment=True
    )


'''
example usage:

PYTHON:
@app.route('/download/<filename>')
def download_route(filename):
    # Call your function
    response =get_file_download(filename)
    
    # already contains the "File not found" message and 404 status.
    return response
    

HTML: (basically its a href thingy)
<h3>Available Files</h3>
<ul>
    {% for file in files %}
    <li>
        {{ file }} 
        <a href="{{ url_for('download_route', filename=file) }}">
            Download
        </a>
    </li>
    {% endfor %}
</ul>
    
'''


def get_channel_stats(department_name: str):
    """Retrieve statistics for a specific department for the Discord report."""
    db = get_database(FILES_DATABASE)
    return db.execute(
        'SELECT file_type, COUNT(*) as count FROM files WHERE department = ? GROUP BY file_type',
        (department_name.upper(),)
    ).fetchall()