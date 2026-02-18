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
    """Maps file extensions to emojis for the UI."""
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
    """Format datetime string to DD-MM-YYYY HH:MM:SS (24h format)."""
    if not datetime_str:
        return 'N/A'
    
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime('%d-%m-%Y %H:%M:%S')
    except (ValueError, AttributeError):
        return str(datetime_str)[:19]

def register_routes(app):
    """Register all routes with the Flask app."""

    register_auth_routes(app)

    @app.route('/update-profile', methods=['POST'])
    def update_profile():
        email = request.form.get('email', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        if email and '@' not in email:
            return "Invalid email format", 400
        
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 8):
            return "Phone number must be exactly 8 digits", 400
        
        db = get_database(USER_DATABASE)
        try:
            db.execute(
                'UPDATE users SET email = ?, phone_number = ? WHERE id = ?',
                (email if email else None, phone_number if phone_number else None, current_user.id)
            )
            db.commit()
            return redirect(url_for('settings'))
        except Exception as e:
            print(f"Error updating profile: {e}")
            return "Failed to update profile", 500
        
    @app.route('/files')
    def files():
        db = get_database(FILES_DATABASE)

        # --- ADDITIONAL FEATURE: STATS SUMMARY ---
        # This aggregates the count of files by source (Discord vs Web)
        stats_query = db.execute('SELECT source, COUNT(*) as count FROM files GROUP BY source').fetchall()
        stats_summary = {row['source']: row['count'] for row in stats_query}

        # Get all unique departments for filter dropdown
        departments_rows = db.execute(
            'SELECT DISTINCT department FROM files ORDER BY department'
        ).fetchall()
        departments = [dept[0] for dept in departments_rows if dept[0]]
        
        selected_dept = request.args.get('department', 'all')
        search_query = request.args.get('search', '').strip()

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

        cursor = db.execute(query, tuple(params)).fetchall()
        files_list = [File.from_row(row) for row in cursor]
    
        return render_template('files.html',
                            files=files_list,
                            stats_summary=stats_summary, # Added for reporting feature
                            departments=departments,
                            selected_dept=selected_dept,
                            search_query=search_query,
                            get_file_icon=get_file_icon,
                            format_datetime=format_datetime)

    @app.route('/download/<filename>')
    def download_file(filename):
        from database_helpers import get_file_download
        return get_file_download(filename)
    
    @app.route('/edit-file/<int:file_id>')
    def edit_file(file_id):
        if current_user.role != 'admin':
            return "Unauthorized - Admin access required", 403
        
        db = get_database(FILES_DATABASE)
        file_data = db.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
        
        if not file_data:
            return "File not found", 404
        
        file = File.from_row(file_data)
        
        departments_rows = db.execute('SELECT DISTINCT department FROM files ORDER BY department').fetchall()
        departments = [dept[0] for dept in departments_rows if dept[0]]
        
        return render_template('edit-file.html', file=file, departments=departments)

    @app.route('/update-file/<int:file_id>', methods=['POST'])
    def update_file(file_id):
        if current_user.role != 'admin':
            return "Unauthorized - Admin access required", 403
        
        file_name = request.form.get('file_name', '').strip()
        department = request.form.get('department', '').strip()
        project = request.form.get('project', '').strip()
        
        if not file_name or not project:
            return "File name and project cannot be empty", 400
        
        if file_name.isdigit() or project.isdigit():
            return "Fields cannot be just numbers", 400
        
        db = get_database(FILES_DATABASE)
        current_file = db.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
        
        if not current_file:
            return "File not found", 404
        
        try:
            db.execute(
                'UPDATE files SET file_name = ?, department = ?, project = ? WHERE id = ?',
                (file_name, department, project, file_id)
            )
            db.commit()
            
            if file_name != current_file['file_name']:
                old_path = os.path.join('downloads', current_file['file_name'])
                new_path = os.path.join('downloads', secure_filename(file_name))
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    db.execute('UPDATE files SET file_path = ? WHERE id = ?', (new_path, file_id))
                    db.commit()
            
            return redirect(url_for('files'))
        except Exception as e:
            print(f"Error updating file: {e}")
            return "Failed to update file", 500

    @app.route('/delete-file/<int:file_id>', methods=['POST'])
    def delete_file(file_id):
        if current_user.role != 'admin':
            return "Unauthorized - Admin access required", 403
        
        db = get_database(FILES_DATABASE)
        file_data = db.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
        
        if not file_data:
            return "File not found", 404
        
        try:
            db.execute('DELETE FROM files WHERE id = ?', (file_id,))
            db.commit()
            
            file_path = os.path.join('downloads', file_data['file_name'])
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return redirect(url_for('files'))
        except Exception as e:
            print(f"Error deleting file: {e}")
            return "Failed to delete file", 500
