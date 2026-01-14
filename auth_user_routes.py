#      -----      {{{     IMPORTS     }}}      -----      #

from flask import render_template, request, redirect, url_for
from database_helpers import get_database, USER_DATABASE

#      -----      {{{     AUTH ROUTES     }}}      -----      #


def register_auth_routes(app):
    """Register authentication routes (login/register) with the Flask app."""

    # Login screen (first screen)
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        db = get_database(USER_DATABASE)  # connects to user database
        error = None

        if request.method == 'POST':
            # Change based on the form field names
            username = request.form.get('username', '')
            password = request.form.get('password', '')  # This too bro

            if not username or not password:
                # Add the error message to whatever u want
                error = 'Username and password are required.'
            else:
                # Check if user exists and password matches
                user = db.execute(
                    # If u adding more login details then change accordingly
                    'SELECT * FROM users WHERE username = ? AND user_password = ?',
                    (username, password)
                ).fetchone()

                if user is not None:
                    # redirects to homepage on successful login
                    return redirect(url_for('home'))
                else:
                    # Add the error message to whatever u want
                    error = 'Invalid username or password.'

        # sends the user to the login page
        return render_template('login.html', error=error)

    # User registration route
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # sends the user to the registration page
        return render_template('register.html')
