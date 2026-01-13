#      -----      {{{     IMPORTS     }}}      -----      #

import sqlite3
import os
from flask import g, Flask

#      -----      {{{     DATABASE CONSTANTS     }}}      -----      #

USER_DATABASE = 'user_data.db'  # 1. User Database
FILES_DATABASE = 'files_data.db'  # 2. Files Database


#      -----      {{{     DATABASE HELPERS     }}}      -----      #


def get_database(db_name: str) -> sqlite3.Connection:
    """Get database connection for the current request context."""
    db_attr = f'_db_{db_name}'

    # Check if connection already exists in this request context
    database = getattr(g, db_attr, None)

    if database is None:
        # Create new connection if it doesn't exist
        database = sqlite3.connect(db_name)
        # Create rows as dictionaries (empty for now)
        database.row_factory = sqlite3.Row
        setattr(g, db_attr, database)  # Stores in Flask's g object

    return database


def init_database(db_name: str, app: Flask) -> None:
    """Initialize database with schema from schemas.sql."""
    with app.app_context():
        database = get_database(db_name)
        with app.open_resource(f'schemas.sql') as f:
            sql_script = f.read().decode('utf-8')
            database.executescript(sql_script)
        database.commit()


def ensure_databases(app: Flask) -> None:
    """Ensures databases are initialized before first request."""
    if not os.path.exists(USER_DATABASE):
        init_database(USER_DATABASE, app)
    if not os.path.exists(FILES_DATABASE):
        init_database(FILES_DATABASE, app)


def close_databases(error) -> None:
    """Close all database connections when the request context ends."""
    # Close user database
    user_db = getattr(g, '_db_' + USER_DATABASE, None)
    if user_db is not None:
        user_db.close()

    # Close files database
    files_db = getattr(g, '_db_' + FILES_DATABASE, None)
    if files_db is not None:
        files_db.close()
