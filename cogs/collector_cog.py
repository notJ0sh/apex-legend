# collector_cog.py
import os
import re
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Import the check from your existing admin_checks file
from .admin_checks import admin_only_check
from database_helpers import add_data_from_discord

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "").strip()


class CollectorCog(commands.Cog):
    """Collects files and links from Discord and sends them to backend."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.collect_active: bool = True
        print(f"CollectorCog initialised. API_BASE_URL={API_BASE_URL!r}")

    # ---------- helpers ----------

    @staticmethod
    def extract_links(text: str) -> list[str]:
        pattern = re.compile(r"(https?://[^\s]+)", re.IGNORECASE)
        return pattern.findall(text or "")

    def build_payload_from_message(self, message: discord.Message) -> dict:
        attachments_data = []
        for att in message.attachments:
            attachments_data.append({
                "filename": att.filename,
                "url": att.url,
                "content_type": att.content_type,
                "size": att.size,
            })

        links = self.extract_links(message.content or "")

        return {
            "message_id": str(message.id),
            "uploader_id": str(message.author.id),
            "uploader_name": message.author.name,
            "channel_id": str(message.channel.id),
            "channel_name": getattr(message.channel, "name", "DM"),
            "content_text": message.content or "",
            "attachments": attachments_data,
            "links": links,
            "timestamp": message.created_at.isoformat(),
        }

    def save_files_to_database(self, message: discord.Message, attachments_data: list[dict]):
        """Save file data to the files table in the database."""
        for att_data in attachments_data:
            file_record = {
                "file_name": att_data["filename"],
                "file_type": att_data["content_type"] or "unknown",
                "file_path": att_data["url"],
                "user": message.author.name,
                "group_name": getattr(message.channel, "name", "DM"),
                "department": "General",
                "source": "discord",
                "user_id": str(message.author.id),
                "message_id": str(message.id),
                "channel_id": str(message.channel.id),
            }
            try:
                add_data_from_discord(file_record)
            except Exception as e:
                print(f"Error saving file to database: {e}")

    # ---------- event listener ----------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore DMs and bot messages
        if message.guild is None or message.author.bot or not self.collect_active:
            return

        has_attachments = len(message.attachments) > 0
        has_links = len(self.extract_links(message.content or "")) > 0

        if not (has_attachments or has_links):
            return

        payload = self.build_payload_from_message(message)
        print(f"Collecting from {message.author} in #{message.channel}")

        if has_attachments:
            self.save_files_to_database(message, payload['attachments'])

    # ---------- slash commands ----------

    @app_commands.command(
        name="enable_collection",
        description="Enable automatic file/link collection."
    )
    @app_commands.check(admin_only_check)
    async def enable_collection(self, interaction: discord.Interaction):
        self.collect_active = True
        await interaction.response.send_message("✅ Collection enabled.")

    @app_commands.command(
        name="disable_collection",
        description="Disable automatic file/link collection."
    )
    @app_commands.check(admin_only_check)
    async def disable_collection(self, interaction: discord.Interaction):
        self.collect_active = False
        await interaction.response.send_message("❌ Collection disabled.")

    @app_commands.command(
        name="collector_status",
        description="Show current collector status."
    )
    async def collector_status(self, interaction: discord.Interaction):
        status = "active ✅" if self.collect_active else "inactive ❌"
        await interaction.response.send_message(f"Collector is currently **{status}**.")

    # Shared error handler for this Cog
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("❌ You do not have the required Admin role.", ephemeral=True)
        else:
            print(f"Cog Command Error: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(CollectorCog(bot))
