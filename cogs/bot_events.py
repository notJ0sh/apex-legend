"""
Discord bot events and event handlers.
"""

import discord
from discord.ext import commands
from discord import app_commands
from .admin_checks import admin_only_check


def setup_bot_events(bot: commands.Bot) -> None:
    """Register all bot events to the bot instance."""

    @bot.event
    async def on_ready():
        """Event triggered when bot successfully logs in."""
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")
        try:
            # Syncs all commands registered to bot.tree (global)
            # This includes the Cog commands since they are added during run_bot()
            synced = await bot.tree.sync()
            print(f"--- Command Sync Report ---")
            print(f"Total synced: {len(synced)}")
            for cmd in synced:
                print(f"-> Synced command: /{cmd.name}")
            print(f"---------------------------")
        except Exception as e:
            print(f"Error syncing commands: {e}")

    @bot.tree.command(name="shutdown", description="Shut down the bot (admin only).")
    @app_commands.check(admin_only_check)
    async def shutdown(interaction: discord.Interaction):
        """Shutdown command for admins."""
        await interaction.response.send_message("Shutting down bot...")
        await bot.close()

    @bot.tree.command(name="ping", description="Ping the bot.")
    async def ping(interaction: discord.Interaction):
        """Ping command to test bot responsiveness."""
        await interaction.response.send_message("Pong!")
