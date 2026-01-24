#      -----      {{{     IMPORTS     }}}      -----      #

from flask import render_template, redirect, url_for, request
from flask_login import current_user
from auth_user_routes import register_auth_routes
from database_helpers import get_database, USER_DATABASE

#      -----      {{{     ROUTES (MAIN EVENTS)     }}}      -----      #


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
