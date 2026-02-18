#      -----      {{{     IMPORTS     }}}      -----      #

import logging
import os
import json
import re  # <--- Regex module
from datetime import datetime, timedelta 
from flask import abort, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from database_helpers import get_database, USER_DATABASE
from models import User

#      -----      {{{     GLOBAL MEMORY     }}}      -----      #
TEMP_NEW_USERS = [] 
MAINTENANCE_FILE = 'maintenance_config.json'

# --- HELPER FUNCTIONS ---
def get_deleted_count():
    if not os.path.exists('deleted_count.txt'): return 0
    with open('deleted_count.txt', 'r') as f:
        try: return int(f.read().strip())
        except ValueError: return 0

def increment_deleted_count():
    current = get_deleted_count()
    new_count = current + 1
    with open('deleted_count.txt', 'w') as f: f.write(str(new_count))
    return new_count

# --- SMART MAINTENANCE CHECK ---
def check_maintenance_lock(user_obj=None):
    if not os.path.exists(MAINTENANCE_FILE):
        return False, None

    try:
        with open(MAINTENANCE_FILE, 'r') as f:
            config = json.load(f)
    except:
        return False, None 

    if not config.get('active', False):
        return False, None

    if user_obj and user_obj.role == 'admin':
        return False, None

    duration = config.get('duration', 'Unknown')
    
    if 'ALL_DEPARTMENTS' in config.get('departments', []):
        return True, duration

    if user_obj:
        if user_obj.department and user_obj.department in config.get('departments', []):
            return True, duration
        if user_obj.username in config.get('users', []):
            return True, duration

    return False, None


#      -----      {{{     AUTH ROUTES     }}}      -----      #

def register_auth_routes(app):

    # --- 0. HOME ROUTE ---
    @app.route('/')
    @app.route('/home')
    def home():
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        is_blocked, duration = check_maintenance_lock(current_user)
        if is_blocked:
            logout_user()
            return render_template('maintenance.html', duration=duration)

        broadcast_msg = None
        if os.path.exists('broadcast.txt'):
            with open('broadcast.txt', 'r') as f:
                content = f.read().strip()
                if content: broadcast_msg = content

        return render_template('homepage.html', broadcast_msg=broadcast_msg)

    # --- 11. PREPARE MAINTENANCE ---
    @app.route('/prepare_maintenance', methods=['POST'])
    @login_required
    def prepare_maintenance():
        if current_user.role != 'admin': abort(403)
        
        password = request.form.get('password')
        if password == "12345":
            db = get_database(USER_DATABASE)
            users = db.execute('SELECT username, user_role FROM users').fetchall()
            all_users = db.execute('SELECT DISTINCT department FROM users').fetchall()
            departments = [row['department'] for row in all_users if row['department']]
            return render_template('maintenance_setup.html', users=users, departments=departments)
        else:
            flash("Wrong Admin Password!", "danger")
            return redirect(url_for('dashboard'))

    # --- 12. CONFIRM MAINTENANCE ---
    @app.route('/confirm_maintenance', methods=['POST'])
    @login_required
    def confirm_maintenance():
        if current_user.role != 'admin': abort(403)
        duration = request.form.get('duration')
        target_depts = request.form.getlist('departments')
        target_users = request.form.getlist('users')
        config = { "active": True, "duration": duration, "departments": target_depts, "users": target_users }
        with open(MAINTENANCE_FILE, 'w') as f: json.dump(config, f)
        flash("Maintenance Mode Activated!", "warning")
        return redirect(url_for('dashboard'))

    # --- 13. DISABLE MAINTENANCE ---
    @app.route('/disable_maintenance')
    @login_required
    def disable_maintenance():
        if current_user.role != 'admin': abort(403)
        if os.path.exists(MAINTENANCE_FILE): os.remove(MAINTENANCE_FILE)
        flash("Maintenance Mode Disabled.", "success")
        return redirect(url_for('dashboard'))

    # --- 10. BROADCAST SYSTEM ---
    @app.route('/post_broadcast', methods=['POST'])
    @login_required
    def post_broadcast():
        if current_user.role != 'admin': abort(403)
        message = request.form.get('message')
        with open('broadcast.txt', 'w') as f: f.write(message)
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
                curr = db.execute('SELECT id, username, user_role, department FROM users WHERE username = ? AND user_password = ?', (username, password))
                user_data = curr.fetchone()

                if user_data:
                    role = user_data['user_role']
                    temp_user = User(id=user_data['id'], username=user_data['username'], user_role=role, department=user_data['department'])
                    
                    is_blocked, duration = check_maintenance_lock(temp_user)
                    if is_blocked: return render_template('maintenance.html', duration=duration)

                    login_user(temp_user)
                    session['user'] = temp_user.username
                    session['role'] = temp_user.role
                    logging.info(f"User: {temp_user.username} | Role: {temp_user.role} | Action: Logged In")
                    
                    if temp_user.role == 'admin': return redirect(url_for('dashboard'))
                    else: return redirect(url_for('home'))
                else:
                    error = 'Invalid username or password.'

        return render_template('login.html', error=error)

    # --- 2. LOGOUT ---
    @app.route('/logout')
    def logout():
        if current_user.is_authenticated:
            logging.info(f"User: {current_user.username} | Action: Logged Out")
        logout_user()
        session.clear()
        return redirect(url_for('login'))

    # --- 3. REGISTER (Fixed with Debugging) ---
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if not current_user.is_authenticated or current_user.role != 'admin': abort(403)
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip() # .strip() removes accidental spaces
            password = request.form.get('password')
            role = request.form.get('role')
            department = request.form.get('department', None)
            
            # --- DEBUGGING PRINT ---
            print(f"DEBUG: Trying to register username: '{username}'")

            # --- VALIDATION CHECK ---
            if not re.match(r'^[a-zA-Z ]+$', username):
                print("DEBUG: >> REGEX FAILED. Name contains invalid characters.")
                return render_template('register.html', error="Invalid Name: Use letters only (No numbers/symbols).")
            else:
                print("DEBUG: >> REGEX PASSED. Name is good.")
            # ------------------------

            db = get_database(USER_DATABASE)
            try:
                db.execute('INSERT INTO users (username, user_password, user_role, department) VALUES (?, ?, ?, ?)', (username, password, role, department))
                db.commit()
                TEMP_NEW_USERS.append({'username': username, 'time': datetime.now()})
                logging.info(f"User: {current_user.username} | Action: Created New User '{username}' ({role})")
                return redirect(url_for('manage_users'))
            except Exception as e:
                print(f"DEBUG: Database Error: {e}") 
                return render_template('register.html', error="Registration failed (Name might be taken).")
        
        return render_template('register.html')

    # --- 4. DASHBOARD ---
    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role != 'admin': return redirect(url_for('home'))

        db = get_database(USER_DATABASE)
        all_users = db.execute('SELECT * FROM users').fetchall()
        active_count = len(all_users)
        deleted_count = get_deleted_count()
        total_count = active_count + deleted_count
        
        new_user_count = 0
        now = datetime.now()
        for user in TEMP_NEW_USERS:
            if now - user['time'] < timedelta(seconds=30): new_user_count += 1
        
        stats = { 'total': total_count, 'active': active_count, 'suspended': deleted_count, 'new': new_user_count }
        pie_data = [['Status', 'Count'], ['Active', stats['active']], ['Deleted', stats['suspended']], ['New', stats['new']]]
        line_data = [['Timeline', 'New Users', 'Active Users'], ['Session Start', 0, max(0, active_count - new_user_count - 1)], ['Pre-Demo', 0, max(0, active_count - 1)], ['LIVE NOW', new_user_count, active_count]]
        
        current_broadcast = ""
        if os.path.exists('broadcast.txt'):
             with open('broadcast.txt', 'r') as f: current_broadcast = f.read().strip()
        
        maintenance_active = False
        if os.path.exists(MAINTENANCE_FILE):
             with open(MAINTENANCE_FILE, 'r') as f:
                try: 
                    conf = json.load(f)
                    if conf.get('active'): maintenance_active = True
                except: pass

        return render_template('dashboard.html', stats=stats, pie_data=pie_data, line_data=line_data, current_broadcast=current_broadcast, maintenance_active=maintenance_active)

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
                    if "Action:" in line or "Starting Flask" in line: filtered_logs.append(line)
                filtered_logs.reverse()
        else: filtered_logs = ["Log file not found."]
        return render_template('logs.html', logs=filtered_logs)