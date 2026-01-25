#      -----      {{{     IMPORTS     }}}      -----      #

from flask import abort, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from database_helpers import get_database, USER_DATABASE
from models import User

#      -----      {{{     AUTH ROUTES     }}}      -----      #

def register_auth_routes(app):
    """Register authentication routes (login/register/dashboard/CRUD) with the Flask app."""

    # --- 1. LOGIN ---
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
                curr = db.execute(
                    'SELECT id, username, user_role, department FROM users WHERE username = ? AND user_password = ?',
                    (username, password)
                )
                user_data = curr.fetchone()

                if user_data:
                    # Create User Object
                    user_obj = User(
                        id=user_data['id'],
                        username=user_data['username'],
                        user_role=user_data['user_role'],
                        department=user_data['department']
                    )
                    login_user(user_obj)
                    
                    # Store session data for Settings/Dashboard
                    session['user'] = user_obj.username
                    session['role'] = user_obj.role
                    
                    # Redirect to Dashboard after login
                    return redirect(url_for('dashboard')) 
                else:
                    error = 'Invalid username or password.'

        return render_template('login.html', error=error)

    # --- 2. LOGOUT ---
    @app.route('/logout')
    def logout():
        logout_user()
        session.clear()
        return redirect(url_for('login'))

    # --- 3. REGISTER ---
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # Only Admins can register new users
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            department = request.form.get('department', None)

            db = get_database(USER_DATABASE)
            existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

            if existing:
                return render_template('register.html', error="Username taken.")

            try:
                db.execute(
                    'INSERT INTO users (username, user_password, user_role, department) VALUES (?, ?, ?, ?)',
                    (username, password, role, department)
                )
                db.commit()
                return redirect(url_for('manage_users'))
            except Exception:
                return render_template('register.html', error="Registration failed.")

        return render_template('register.html')

    # --- 4. DASHBOARD ---
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Mock Data for Charts
        stats = { 'total': 1400, 'active': 1233, 'suspended': 145, 'new': 22 }

        pie_data = [
            ['Status', 'Count'],
            ['Active', stats['active']],
            ['Suspended', stats['suspended']],
            ['New', stats['new']]
        ]

        line_data = [
            ['Month', 'New Users', 'Total Users'],
            ['Jan',  50,       400],
            ['Feb',  80,       480],
            ['Mar',  100,      580],
            ['Apr',  150,      730],
            ['May',  200,      930],
            ['Jun',  250,      1180]
        ]

        return render_template('dashboard.html', 
                               stats=stats, 
                               pie_data=pie_data, 
                               line_data=line_data)

    # --- 5. MANAGE USERS ---
    @app.route('/manage-users')
    @login_required
    def manage_users():
        if current_user.role != 'admin': abort(403)
        db = get_database(USER_DATABASE)
        users = db.execute('SELECT * FROM users').fetchall()
        return render_template('manage_users.html', users=users)

    # --- 6. EDIT USER ---
    @app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    def edit_user(user_id):
        if current_user.role != 'admin': abort(403)
        db = get_database(USER_DATABASE)

        if request.method == 'POST':
            username = request.form.get('username')
            role = request.form.get('role')
            department = request.form.get('department')
            
            db.execute('UPDATE users SET username = ?, user_role = ?, department = ? WHERE id = ?', 
                       (username, role, department, user_id))
            db.commit()
            return redirect(url_for('manage_users'))

        user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return render_template('edit-user.html', user=user_row)

    # --- 7. DELETE USER ---
    @app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    def delete_user(user_id):
        if current_user.role != 'admin': abort(403)
        db = get_database(USER_DATABASE)
        
        if request.method == 'POST':
            db.execute('DELETE FROM users WHERE id = ?', (user_id,))
            db.commit()
            return redirect(url_for('manage_users'))

        user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return render_template('delete-user.html', user=user_row)

    # --- 8. SETTINGS ---
    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html')
