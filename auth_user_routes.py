#      -----      {{{     IMPORTS     }}}      -----      #

import logging
import os
from datetime import datetime, timedelta 
from flask import abort, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from database_helpers import get_database, USER_DATABASE
from models import User

#      -----      {{{     GLOBAL MEMORY (For Demo)     }}}      -----      #
TEMP_NEW_USERS = [] 

# Helper function to handle the Deleted Count File
def get_deleted_count():
    if not os.path.exists('deleted_count.txt'):
        return 0
    with open('deleted_count.txt', 'r') as f:
        try:
            return int(f.read().strip())
        except ValueError:
            return 0

def increment_deleted_count():
    current = get_deleted_count()
    new_count = current + 1
    with open('deleted_count.txt', 'w') as f:
        f.write(str(new_count))
    return new_count

#      -----      {{{     AUTH ROUTES     }}}      -----      #

def register_auth_routes(app):
    """Register authentication routes."""

    # --- 0. HOME ROUTE (Updated to Read Broadcast) ---
    @app.route('/')
    @app.route('/home')
    def home():
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        # READ BROADCAST MESSAGE
        broadcast_msg = None
        if os.path.exists('broadcast.txt'):
            with open('broadcast.txt', 'r') as f:
                content = f.read().strip()
                if content: # Only show if not empty
                    broadcast_msg = content

        return render_template('homepage.html', broadcast_msg=broadcast_msg)

    # --- 10. BROADCAST SYSTEM (New Feature) ---
    @app.route('/post_broadcast', methods=['POST'])
    @login_required
    def post_broadcast():
        if current_user.role != 'admin': abort(403)
        
        message = request.form.get('message')
        
        # Save message to a text file
        with open('broadcast.txt', 'w') as f:
            f.write(message)
            
        return redirect(url_for('dashboard'))

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
                    user_obj = User(
                        id=user_data['id'],
                        username=user_data['username'],
                        user_role=user_data['user_role'],
                        department=user_data['department']
                    )
                    login_user(user_obj)
                    session['user'] = user_obj.username
                    session['role'] = user_obj.role
                    logging.info(f"User: {user_obj.username} | Role: {user_obj.role} | Action: Logged In")
                    
                    if user_obj.role == 'admin':
                        return redirect(url_for('dashboard'))
                    else:
                        return redirect(url_for('home'))
                else:
                    error = 'Invalid username or password.'

        return render_template('login.html', error=error)

    # --- 2. LOGOUT ---
    @app.route('/logout')
    def logout():
        user_name = current_user.username if current_user.is_authenticated else "Unknown"
        if user_name != "Unknown":
            logging.info(f"User: {user_name} | Action: Logged Out")
        logout_user()
        session.clear()
        return redirect(url_for('login'))

    # --- 3. REGISTER ---
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if not current_user.is_authenticated or current_user.role != 'admin': abort(403)

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
                db.execute('INSERT INTO users (username, user_password, user_role, department) VALUES (?, ?, ?, ?)', (username, password, role, department))
                db.commit()
                TEMP_NEW_USERS.append({'username': username, 'time': datetime.now()})
                logging.info(f"User: {current_user.username} | Action: Created New User '{username}' ({role})")
                return redirect(url_for('manage_users'))
            except Exception:
                return render_template('register.html', error="Registration failed.")

        return render_template('register.html')

    # --- 4. DASHBOARD ---
    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role != 'admin':
            return redirect(url_for('home'))

        db = get_database(USER_DATABASE)
        all_users = db.execute('SELECT * FROM users').fetchall()
        active_count = len(all_users)
        deleted_count = get_deleted_count()
        total_count = active_count + deleted_count
        
        new_user_count = 0
        now = datetime.now()
        for user in TEMP_NEW_USERS:
            if now - user['time'] < timedelta(seconds=30):
                new_user_count += 1
        
        stats = { 'total': total_count, 'active': active_count, 'suspended': deleted_count, 'new': new_user_count }
        pie_data = [['Status', 'Count'], ['Active', stats['active']], ['Deleted', stats['suspended']], ['New', stats['new']]]
        line_data = [
            ['Timeline', 'New Users', 'Active Users'], 
            ['Session Start', 0, max(0, active_count - new_user_count - 1)], 
            ['Pre-Demo', 0, max(0, active_count - 1)], 
            ['LIVE NOW', new_user_count, active_count]
        ]
        
        # Read current broadcast for dashboard display
        current_broadcast = ""
        if os.path.exists('broadcast.txt'):
             with open('broadcast.txt', 'r') as f:
                current_broadcast = f.read().strip()

        return render_template('dashboard.html', stats=stats, pie_data=pie_data, line_data=line_data, current_broadcast=current_broadcast)

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
            db.execute('UPDATE users SET username = ?, user_role = ?, department = ? WHERE id = ?', (username, role, department, user_id))
            db.commit()
            logging.info(f"User: {current_user.username} | Action: Edited User ID {user_id}")
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
            increment_deleted_count()
            db.execute('DELETE FROM users WHERE id = ?', (user_id,))
            db.commit()
            logging.info(f"User: {current_user.username} | Action: Deleted User ID {user_id}")
            return redirect(url_for('manage_users'))
        user_row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return render_template('delete-user.html', user=user_row)

    # --- 8. SETTINGS ---
    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html')

    # --- 9. LOGS ---
    @app.route('/logs')
    @login_required
    def logs():
        if current_user.role != 'admin': abort(403)
        log_path = 'Logs/app_activity.txt'
        filtered_logs = []
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if "Action:" in line or "Starting Flask" in line:
                        filtered_logs.append(line)
                filtered_logs.reverse()
        else:
            filtered_logs = ["Log file not found."]
        return render_template('logs.html', logs=filtered_logs)