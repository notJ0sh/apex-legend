#      -----      {{{     IMPORTS     }}}      -----      #

from flask import render_template, redirect, url_for, request
from flask_login import current_user
from auth_user_routes import register_auth_routes
from database_helpers import get_database, USER_DATABASE, get_files_by_department, FILES_DATABASE
from models import File
import os
from werkzeug.utils import secure_filename

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
    
    #Shows the edit form
    @app.route('/edit-file/<int:file_id>')
    def edit_file(file_id):
        # Check if user is admin
        if current_user.role != 'admin':
            return "Unauthorized - Admin access required", 403
        
        # Get file data from database
        db = get_database(FILES_DATABASE)
        file_data = db.execute(
            'SELECT * FROM files WHERE id = ?', 
            (file_id,)
        ).fetchone()
        
        if not file_data:
            return "File not found", 404
        
        # Convert to File object
        file = File.from_row(file_data)
        
        # Get all departments for dropdown
        departments = db.execute(
            'SELECT DISTINCT department FROM files ORDER BY department'
        ).fetchall()
        departments = [dept[0] for dept in departments if dept[0]]
        
        return render_template('edit-file.html', 
                            file=file, 
                            departments=departments)

    #Actually processes the form submissions 
    @app.route('/update-file/<int:file_id>', methods=['POST'])
    def update_file(file_id):
        # Check if user is admin
        if current_user.role != 'admin':
            return "Unauthorized - Admin access required", 403
        
        # Get form data
        file_name = request.form.get('file_name', '').strip()
        department = request.form.get('department', '').strip()
        project = request.form.get('project', '').strip()
        
        # Validation
        if not file_name:
            return "File name cannot be empty", 400
        
        if not project:
            return "Project cannot be empty", 400
        
        # Check if file name is just numbers
        if file_name.isdigit():
            return "File name cannot be just numbers", 400
        
        # Check if project is just numbers
        if project.isdigit():
            return "Project cannot be just numbers", 400
        
        # Get current file data
        db = get_database(FILES_DATABASE)
        current_file = db.execute(
            'SELECT * FROM files WHERE id = ?', 
            (file_id,)
        ).fetchone()
        
        if not current_file:
            return "File not found", 404
        
        # Check if file name already exists (excluding current file)
        existing_file = db.execute(
            'SELECT id FROM files WHERE file_name = ? AND id != ?', 
            (file_name, file_id)
        ).fetchone()
        
        if existing_file:
            return f"File name '{file_name}' already exists", 400
        
        # Update file in database
        try:
            db.execute(
                '''UPDATE files 
                SET file_name = ?, department = ?, project = ?
                WHERE id = ?''',
                (file_name, department, project, file_id)
            )
            db.commit()
            
            # Rename the actual file if file name changed
            if file_name != current_file['file_name']:
                old_path = os.path.join('downloads', current_file['file_name'])
                new_path = os.path.join('downloads', secure_filename(file_name))
                
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    # Update file_path in database
                    db.execute(
                        'UPDATE files SET file_path = ? WHERE id = ?',
                        (new_path, file_id)
                    )
                    db.commit()
            
            return redirect(url_for('files'))
            
        except Exception as e:
            print(f"Error updating file: {e}")
            return "Failed to update file", 500

    #Delete files
    @app.route('/delete-file/<int:file_id>', methods=['POST'])
    def delete_file(file_id):
        # Check if user is admin
        if current_user.role != 'admin':
            return "Unauthorized - Admin access required", 403
        
        # Get file data first
        db = get_database(FILES_DATABASE)
        file_data = db.execute(
            'SELECT * FROM files WHERE id = ?', 
            (file_id,)
        ).fetchone()
        
        if not file_data:
            return "File not found", 404
        
        try:
            # Delete file from database
            db.execute('DELETE FROM files WHERE id = ?', (file_id,))
            db.commit()
            
            # Delete actual file from downloads folder
            file_path = os.path.join('downloads', file_data['file_name'])
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return redirect(url_for('files'))
            
        except Exception as e:
            print(f"Error deleting file: {e}")
            return "Failed to delete file", 500