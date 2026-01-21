#      -----      {{{     IMPORTS     }}}      -----      #

import os
import asyncio
import threading
from dotenv import load_dotenv

from flask import Flask
from flask_login import LoginManager
from database_helpers import ensure_databases, close_databases, get_database, USER_DATABASE
from models import User
from app_routes import register_routes

import logging
from log_handler import setup_logging

# Discord bot imports
import discord
from discord.ext import commands
from cogs.bot_events import setup_bot_events

# Init logging
setup_logging()

# Init login manager
login_manager = LoginManager()

# Load environment variables
load_dotenv()

# Discord bot configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admin")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in .env")


#      -----      {{{     SET UP     }}}      -----      #

# Set up app with custom templates and static folders
app = Flask(__name__, template_folder='templates (HTML pages)',
            static_folder='static (css styles)')

# Get secret key
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fd7gs6h9guohejtbgisfu")


# Link login manager to app
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Register all routes
register_routes(app)

# ----- Discord Bot Setup -----
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.members = True

# bot instance
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Setup bot events and global commands
setup_bot_events(bot)

# How to load user


@login_manager.user_loader
def load_user(user_id):
    db = get_database(USER_DATABASE)
    user_data = db.execute(
        'SELECT id, username, user_role, department FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if user_data:
        return User(
            id=user_data[0],
            username=user_data[1],
            user_role=user_data[2],
            department=user_data[3]
        )
    return None

#      -----      {{{     BOT AND FLASK COORDINATION     }}}      -----      #


# Global event loop for the bot
bot_loop = None


async def run_bot():
    """Run the Discord bot."""
    async with bot:
        # Load Cog FIRST so the sync in bot_events picks it up
        try:
            await bot.load_extension("cogs.collector_cog")
            print("Loaded collector_cog.")
        except Exception as e:
            print(f"Failed to load collector_cog: {e}")

        # This starts the connection; on_ready will handle the tree sync
        await bot.start(DISCORD_TOKEN)


def start_bot_thread():
    """Start the Discord bot in a background thread."""
    global bot_loop

    def run_async_loop():
        global bot_loop
        bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(bot_loop)
        try:
            bot_loop.run_until_complete(run_bot())
        except Exception as e:
            print(f"Bot error: {e}")
        finally:
            bot_loop.close()

    bot_thread = threading.Thread(target=run_async_loop, daemon=True)
    bot_thread.start()
    print("Discord bot thread initialized.")


#      -----      {{{     SAFETY EVENT HANDLERS     }}}      -----      #

@app.before_request
def before_request() -> None:
    ensure_databases(app)


@app.teardown_appcontext
def teardown_appcontext(error) -> None:
    close_databases(error)


#      -----      {{{     RUN APP     }}}      -----      #

if __name__ == '__main__':
    # Initialize databases BEFORE starting bot
    with app.app_context():
        ensure_databases(app)

    # Start the Discord bot in background thread
    start_bot_thread()

    # Initial log entry
    logging.info("Starting Flask Web Server...")

    # Start Flask web server on main thread
    # use_reloader=False is critical to prevent the bot thread from starting twice
    app.run(debug=True, use_reloader=False)
