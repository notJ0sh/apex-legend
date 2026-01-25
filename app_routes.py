#      -----      {{{     IMPORTS     }}}      -----      #

from flask import render_template, redirect, url_for, request
from flask_login import current_user
from auth_user_routes import register_auth_routes
from database_helpers import get_database, USER_DATABASE, get_files_by_department, FILES_DATABASE
from models import File

#      -----      {{{     ROUTES (MAIN EVENTS)     }}}      -----      #
def get_file_icon(file_type):
    icon_map = {
        'pdf': '📄',
        'word': '📄',
        'doc': '📝',
        'docx': '📝',
        'ppt': '📊',
        'pptx': '📊',
        'xls': '📈',
        'xlsx': '📈',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'zip': '📦',
        'txt': '📃',
        'csv': '📋'
    }
    return icon_map.get(file_type.lower(), '📎')

def format_datetime(datetime_str):
    """Format datetime string to DD-MM-YYYY HH:MM:SS (24h format)"""
    if not datetime_str:
        return 'N/A'
    
    try:
        # Parse the datetime string
        from datetime import datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        # Format to DD-MM-YYYY HH:MM:SS
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    except (ValueError, AttributeError):
        return str(datetime_str)[:19]  # Fallback to original format

def register_routes(app):
    """Register all routes with the Flask app."""

    # Instantly redirect to login screen
    @app.route('/')
    def index():
        return redirect(url_for('login'))

    # Register authentication routes (login/register)
    register_auth_routes(app)

    # Homepage screen
    @app.route('/home')
    def home():
        # sends the user to the homepage
        return render_template('dashboard.html')
    
    #Settings page
    @app.route('/settings')
    def settings():
        # Fetch the current user's email and phone from database
        db = get_database(USER_DATABASE)
        user_data = db.execute(
            'SELECT email, phone_number FROM users WHERE id = ?',
            (current_user.id,)
        ).fetchone()
        
        email = user_data[0] if user_data else None
        phone_number = user_data[1] if user_data else None
        
        return render_template('settings.html', 
                             user_email=email, 
                             user_phone=phone_number)
    
    #Validation for updating user's details
    @app.route('/update-profile', methods=['POST'])
    def update_profile():
        """Update user's email and phone number."""
        email = request.form.get('email', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        if email and '@' not in email:
            return "Invalid email format", 400
        
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 8):
            return "Phone number must be exactly 8 digits", 400
        
        # Update database
        db = get_database(USER_DATABASE)
        try:
            db.execute(
                '''UPDATE users 
                SET email = ?, phone_number = ?
                WHERE id = ?''',
                (email if email else None, 
                phone_number if phone_number else None, 
                current_user.id)
            )
            db.commit()
            return redirect(url_for('settings'))
        except Exception as e:
            print(f"Error updating profile: {e}")
            return "Failed to update profile", 500
        
    # Files repository page
    @app.route('/files')
    def files():
        # Get all unique departments for filter dropdown
        db = get_database(FILES_DATABASE)
        departments = db.execute(
            'SELECT DISTINCT department FROM files ORDER BY department'
        ).fetchall()
        departments = [dept[0] for dept in departments if dept[0]]
        
        # Get selected department from query parameter
        selected_dept = request.args.get('department', 'all')
        search_query = request.args.get('search', '').strip()

        #Build queries based on filters
        query = 'SELECT * FROM files'
        conditions = []
        params = []

        if selected_dept and selected_dept != 'all':
            conditions.append('department = ?')
            params.append(selected_dept)

        if search_query:
            conditions.append('file_name LIKE ?')
            params.append(f'%{search_query}%')
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY time_stamp DESC'

        #Execute query
        cursor = db.execute(query, tuple(params)).fetchall()
        files_list = [File.from_row(row) for row in cursor]
    
        return render_template('files.html',
                            files=files_list,
                            departments=departments,
                            selected_dept=selected_dept,
                            search_query=search_query,
                            get_file_icon=get_file_icon,
                            format_datetime=format_datetime)

    # Download route (add this too)
    @app.route('/download/<filename>')
    def download_file(filename):
        from database_helpers import get_file_download
        return get_file_download(filename)
    
    # Edit file route
    @app.route('/edit-file/<int:file_id>')
    def edit_file(file_id):
        # We'll implement this later - for now just show a placeholder
        return f"Edit file page for file ID: {file_id} - To be implemented"

    # Delete file route
    @app.route('/delete-file/<int:file_id>', methods=['POST'])
    def delete_file(file_id):
        # We'll implement this later - for now just show a placeholder
        return f"Delete file for file ID: {file_id} - To be implemented"