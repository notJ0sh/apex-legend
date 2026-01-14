# collector_cog.py
import os
import re
import aiohttp
import discord

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "").strip()
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admin")


def has_admin_role(member: discord.Member) -> bool:
    for role in member.roles:
        if role.name == ADMIN_ROLE_NAME:
            return True
    return False


def admin_only_check(interaction: discord.Interaction) -> bool:
    if not isinstance(interaction.user, discord.Member):
        raise app_commands.CheckFailure("Not a guild member.")
    if not has_admin_role(interaction.user):
        raise app_commands.CheckFailure(
            "You do not have the required admin role.")
    return True


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
        attachments_data: list[dict] = []
        for att in message.attachments:
            attachments_data.append(
                {
                    "filename": att.filename,
                    "url": att.url,
                    "content_type": att.content_type,
                    "size": att.size,
                }
            )

        links = self.extract_links(message.content or "")

        payload = {
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
        return payload

    async def send_to_backend(self, payload: dict):
        if not API_BASE_URL:
            print("API_BASE_URL not configured, skipping send.")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_BASE_URL, json=payload) as resp:
                    if resp.status not in (200, 201):
                        text = await resp.text()
                        print(f"Backend error {resp.status}: {text}")
                    else:
                        print("Successfully sent payload to backend.")
        except Exception as e:
            print(f"Error sending data to backend: {e}")

    # ---------- event listener ----------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore DMs and bot messages
        if message.guild is None:
            return
        if message.author.bot:
            return

        # Collector disabled
        if not self.collect_active:
            return

        has_attachments = len(message.attachments) > 0
        has_links = len(self.extract_links(message.content or "")) > 0

        if not has_attachments and not has_links:
            return

        payload = self.build_payload_from_message(message)
        print(
            f"Collecting from {message.author} in #{message.channel}: "
            f"{len(payload['attachments'])} attachments, {len(payload['links'])} links"
        )
        await self.send_to_backend(payload)

    # ---------- slash commands ----------

    @app_commands.command(
        name="enable_collection",
        description="Enable automatic file/link collection.",
    )
    @app_commands.check(admin_only_check)
    async def enable_collection(self, interaction: discord.Interaction):
        self.collect_active = True
        await interaction.response.send_message("✅ Collection enabled.")

    @app_commands.command(
        name="disable_collection",
        description="Disable automatic file/link collection.",
    )
    @app_commands.check(admin_only_check)
    async def disable_collection(self, interaction: discord.Interaction):
        self.collect_active = False
        await interaction.response.send_message("❌ Collection disabled.")

    @app_commands.command(
        name="collector_status",
        description="Show collector status and API endpoint.",
    )
    async def collector_status(self, interaction: discord.Interaction):
        status = "active ✅" if self.collect_active else "inactive ❌"
        await interaction.response.send_message(
            f"Collector is currently **{status}**.\n"
            f"API endpoint: `{API_BASE_URL or 'NOT CONFIGURED'}`"
        )

    # shared error handler for admin-only commands
    @enable_collection.error
    @disable_collection.error
    async def admin_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ An error occurred: {error}", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(CollectorCog(bot))
