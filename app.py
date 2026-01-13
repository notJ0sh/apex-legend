#      -----      {{{     IMPORTS     }}}      -----      #

from flask import Flask
from database_helpers import ensure_databases, close_databases
from app_routes import register_routes


#      -----      {{{     SET UP     }}}      -----      #


# Set up app with custom templates and static folders
app = Flask(__name__, template_folder='templates (HTML pages)',
            static_folder='static (css styles)')

# Register all routes
register_routes(app)


#      -----      {{{     SAFETY EVENT HANDLERS     }}}      -----      #


# Ensures databases are initialized before first request
@app.before_request
def before_request() -> None:
    ensure_databases(app)


# Ensures databases are closed after request
@app.teardown_appcontext
def teardown_appcontext(error) -> None:
    close_databases(error)


#      -----      {{{     RUN APP     }}}      -----      #


if __name__ == '__main__':
    app.run(debug=True)
