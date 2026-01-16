#      -----      {{{     IMPORTS     }}}      -----      #

from flask import render_template, redirect, url_for, request
from auth_user_routes import register_auth_routes

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
        return render_template('homepage.html')
