#      -----      {{{     IMPORTS     }}}      -----      #

from flask import render_template, request, redirect, url_for
from database_helpers import get_database, USER_DATABASE

#      -----      {{{     ROUTES (MAIN EVENTS)     }}}      -----      #


def register_routes(app):
    """Register all routes with the Flask app."""

    # Instantly redirect to login screen
    @app.route('/')
    def index():
        return redirect(url_for('login'))

    # Login screen (first screen)
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        db = get_database(USER_DATABASE)  # connects to user database
        error = None

        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')

            if not username or not password:
                error = 'Username and password are required.'
            else:
                # Check if user exists and password matches
                user = db.execute(
                    'SELECT * FROM users WHERE username = ? AND user_password = ?',
                    (username, password)
                ).fetchone()

                if user is not None:
                    # redirects to homepage on successful login
                    return redirect(url_for('home'))
                else:
                    error = 'Invalid username or password.'

        # sends the user to the login page
        return render_template('login.html', error=error)

    # Homepage screen
    @app.route('/home')
    def home():
        # sends the user to the homepage
        return render_template('homepage.html')

    # User registration route
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # sends the user to the registration page
        return render_template('register.html')
