#      -----      {{{     IMPORTS     }}}      -----      #

import sqlite3
import os
from flask import g, Flask

#      -----      {{{     DATABASE CONSTANTS     }}}      -----      #

USER_DATABASE = 'user_data.db'
FILES_DATABASE = 'files_data.db'


#      -----      {{{     DATABASE HELPERS     }}}      -----      #


def get_database(db_name: str) -> sqlite3.Connection:
    """Get database connection for the current request context."""
    db_attr = f'_db_{db_name}'
    database = getattr(g, db_attr, None)

    if database is None:
        database = sqlite3.connect(db_name)
        database.row_factory = sqlite3.Row
        setattr(g, db_attr, database)

    return database


def init_database(db_name: str, schema_file: str, app: Flask) -> None:
    """Initialize database with schema from specified SQL file."""
    with app.app_context():
        database = get_database(db_name)
        with app.open_resource(schema_file) as f:
            sql_script = f.read().decode('utf-8')
            database.executescript(sql_script)
        database.commit()


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


def close_databases(error) -> None:
    """Close all database connections when the request context ends."""
    user_db = getattr(g, '_db_' + USER_DATABASE, None)
    if user_db is not None:
        user_db.close()

    files_db = getattr(g, '_db_' + FILES_DATABASE, None)
    if files_db is not None:
        files_db.close()


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


def add_user_data(data: dict) -> None:
    add_data(USER_DATABASE, 'users', data)


def add_file_data(data: dict) -> None:
    add_data(FILES_DATABASE, 'files', data)
