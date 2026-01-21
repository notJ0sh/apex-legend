#      -----      {{{     IMPORTS     }}}      -----      #

from flask import abort, render_template, request, redirect, url_for
from flask_login import login_required, login_user, logout_user, current_user
from database_helpers import get_database, USER_DATABASE
from models import User

#      -----      {{{     AUTH ROUTES     }}}      -----      #


def register_auth_routes(app):
    """Register authentication routes (login/register) with the Flask app."""

    # Login screen (first screen)
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        db = get_database(USER_DATABASE)
        error = None

        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')

            if not username or not password:
                error = 'Username and password are required.'
            else:
                # Fetch the user
                curr = db.execute(
                    'SELECT id, username, user_role FROM users WHERE username = ? AND user_password = ?',
                    (username, password)
                )
                user_data = curr.fetchone()

                if user_data:
                    # 1. Create the User object from DB data
                    user_obj = User(
                        id=user_data[0],
                        username=user_data[1],
                        user_role=user_data[2]  # Match the name here too!
                    )

                    # 2. Tell Flask-Login to log them in (sets the session cookie)
                    login_user(user_obj)

                    return redirect(url_for('home'))
                else:
                    error = 'Invalid username or password.'

        return render_template('login.html', error=error)

    @app.route('/logout')
    def logout():
        logout_user()  # Clears the session cookie
        return redirect(url_for('login'))

    # User registration route
    @app.route('/register', methods=['GET', 'POST'])
    def register():

        # Only Admins can register new users (remove if u want open registration)
        if current_user.role != 'admin':
            abort(403)  # Forbidden

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            department = request.form.get('department', None)

            db = get_database(USER_DATABASE)

            # 1. Check if username already exists
            existing_user = db.execute(
                'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone()

            if existing_user:
                return render_template('register.html', error="Username already taken.")

            # 2. Hash the password (Optional but HIGHLY recommended)
            # hashed_pw = generate_password_hash(password)
            # If you use hashing, change password to hashed_pw in the query below

            # 3. Insert new user with default role 'user'
            try:
                db.execute(
                    '''INSERT INTO users (username, user_password, user_role, department) 
                       VALUES (?, ?, ?, ?)''',
                    (username, password, role, department)
                )
                db.commit()  # Save changes to the .db file
                return redirect(url_for('login'))
            except Exception as e:
                return render_template('register.html', error="Registration failed.")

        return render_template('register.html')

    # Manage users route
    @app.route('/manage-users')
    @login_required
    def manage_users():
        # SECURITY: Only admins can see this page
        if current_user.role != 'admin':
            abort(403)

        db = get_database(USER_DATABASE)
        # Fetch all users to display in the table
        users = db.execute(
            'SELECT id, username, user_role, department FROM users'
        ).fetchall()

        return render_template('users.html', users=users)
