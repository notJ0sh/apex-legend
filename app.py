#      -----      {{{     IMPORTS     }}}      -----      #

import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, g, jsonify


#      -----      {{{     SET UP     }}}      -----      #


# Set up app
app = Flask(__name__)

# Set up databases
USER_DATABASE = 'user_data.db'  # 1. User Database
FILES_DATABASE = 'files_data.db'  # 2. Files Database


#      -----      {{{     DATABASE HELPERS     }}}      -----      #


# Function to get database connection


def get_database(db_name: str) -> sqlite3.Connection:

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

# Function to initialize databases


def init_database(db_name: str) -> None:
    with app.app_context():

        db_attr = f'_db_{db_name}'
        database = get_database(db_name)
        with app.open_resource(f'schema.sql') as f:
            database.executescript(f.read())
        database.commit()


#      -----      {{{     SAFETY EVENT HANDLERS     }}}      -----      #


# Ensures databases are initialized before first request


@app.before_request
def ensure_databases() -> None:
    if not os.path.exists(USER_DATABASE):
        init_database(USER_DATABASE)
    if not os.path.exists(FILES_DATABASE):
        init_database(FILES_DATABASE)

# Ensures databases are closed after request


@app.teardown_appcontext
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


#      -----      {{{     ROUTES (MAIN EVENTS)     }}}      -----      #


# Login screen (first screen)
@app.route('/', methods=['GET', 'POST'])
def login():
    db = get_database(USER_DATABASE)  # connects to user database

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists and password matches
        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()

        if user is not None:
            # redirects to homepage on successful login
            return redirect(url_for('home'))

    return render_template('login.html')  # sends the user to the login page


# Homepage screen
@app.route('/home')
def home():
    return render_template('homepage.html')  # sends the user to the homepage


# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    # sends the user to the registration page
    return render_template('register.html')
