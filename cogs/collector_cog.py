# cogs/collector_cog.py
import os
import re
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Import the Flask app instance to provide application context
from app import app
# Import the check and database helpers
from .admin_checks import admin_only_check
from database_helpers import add_data_from_discord, get_database, FILES_DATABASE

load_dotenv()

# SECURITY CONFIGURATION
# Whitelist of accepted file extensions. Any file not in this list is rejected.
ALLOWED_EXTENSIONS = {
    '.pdf', '.xlsx', '.xls', '.csv', 
    '.docx', '.doc', '.pptx', '.ppt', 
    '.txt', '.png', '.jpg', '.jpeg', '.gif'
}

class CollectorCog(commands.Cog):
    """Collects files and links from Discord and provides data reporting."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.collect_active: bool = True
        print("CollectorCog initialised.")

    # ---------- helpers ----------

    @staticmethod
    def extract_links(text: str) -> list[str]:
        """Extracts URLs from message content."""
        pattern = re.compile(r"(https?://[^\s]+)", re.IGNORECASE)
        return pattern.findall(text or "")

    def build_payload_from_message(self, message: discord.Message) -> dict:
        """Structures message data for processing."""
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
            "channel_name": getattr(message.channel, "name", "DM").upper(),
            "content_text": message.content or "",
            "attachments": attachments_data,
            "links": links,
            "timestamp": message.created_at.isoformat(),
        }

    def save_files_to_database(self, message: discord.Message, attachments_data: list[dict]):
        """Save file data with a check for duplicates to ensure data integrity."""
        # Wrap database access in the app context for background threads
        with app.app_context():
            try:
                db = get_database(FILES_DATABASE)
                
                for att_data in attachments_data:
                    # Integrity Check: Check if this specific message and file name already exist
                    exists = db.execute(
                        'SELECT id FROM files WHERE file_name = ? AND message_id = ?', 
                        (att_data["filename"], str(message.id))
                    ).fetchone()
                    
                    if exists:
                        continue

                    file_record = {
                        "file_name": att_data["filename"],
                        "file_type": att_data["content_type"] or "unknown",
                        "file_path": att_data["url"],
                        "user": message.author.name,
                        "group_name": getattr(message.channel, "name", "DM"),
                        "department": getattr(message.channel, "name", "N/A").upper(),
                        "source": "discord",
                        "user_id": str(message.author.id),
                        "message_id": str(message.id),
                        "channel_id": str(message.channel.id),
                    }
                    add_data_from_discord(file_record)
            except Exception as e:
                print(f"Error in save_files_to_database: {e}")

    # ---------- ADDITIONAL FEATURE: REPORTING ----------

    @app_commands.command(
        name="generate_report",
        description="Generate a summary of collected data for this channel's department."
    )
    @app_commands.check(admin_only_check)
    async def generate_report(self, interaction: discord.Interaction):
        """Generates a summary report of files collected for the current department."""
        # 1. Defer the response to prevent "Application did not respond"
        await interaction.response.defer()
        
        try:
            dept_name = getattr(interaction.channel, "name", "N/A").upper()
            
            # Wrap database access in the app context
            with app.app_context():
                db = get_database(FILES_DATABASE)
                
                # Aggregate data for the report
                stats = db.execute(
                    'SELECT file_type, COUNT(*) as count FROM files WHERE department = ? GROUP BY file_type', 
                    (dept_name,)
                ).fetchall()
            
            if not stats:
                return await interaction.followup.send(f"No data found for department: **{dept_name}**")

            report_msg = f"📊 **Department Activity Report: {dept_name}**\n"
            total_files = sum(row['count'] for row in stats)
            report_msg += f"Total Assets Collected: `{total_files}`\n\n**File Type Breakdown:**\n"
            
            for row in stats:
                report_msg += f"- {row['file_type'].upper()}: {row['count']}\n"
                
            await interaction.followup.send(report_msg)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    # ---------- event listener ----------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot or not self.collect_active:
            return

        has_attachments = len(message.attachments) > 0
        if not has_attachments:
            return

        # --- SECURITY CHECK START ---
        # Scan all attachments for malicious file extensions before processing
        for attachment in message.attachments:
            # Get file extension (e.g., 'report.pdf' -> '.pdf')
            _, file_extension = os.path.splitext(attachment.filename)
            file_extension = file_extension.lower()

            if file_extension not in ALLOWED_EXTENSIONS:
                # Create a security alert embed
                embed = discord.Embed(
                    title="🚨 Security Alert: Upload Rejected",
                    description=f"The file `{attachment.filename}` was blocked by the security system.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Reason", 
                    value="Unauthorized file type detected. This restriction prevents potential malware or scripts from entering the database.",
                    inline=False
                )
                embed.add_field(
                    name="Allowed Formats", 
                    value="`" + "`, `".join(sorted(ALLOWED_EXTENSIONS)) + "`",
                    inline=False
                )
                embed.set_footer(text="Apex Legend Security Protocol")
                
                # Send the warning to the channel
                await message.channel.send(embed=embed)
                
                # Log to console for admin visibility
                print(f"[SECURITY BLOCK] Prevented {message.author} from uploading: {attachment.filename}")
                
                # Stop processing this message entirely so it doesn't get saved
                return 
        # --- SECURITY CHECK END ---

        # If we passed the check, proceed with saving
        payload = self.build_payload_from_message(message)
        self.save_files_to_database(message, payload['attachments'])

    # ---------- slash commands ----------

    @app_commands.command(name="enable_collection", description="Enable automatic collection.")
    @app_commands.check(admin_only_check)
    async def enable_collection(self, interaction: discord.Interaction):
        self.collect_active = True
        await interaction.response.send_message("✅ Collection enabled.")

    @app_commands.command(name="disable_collection", description="Disable automatic collection.")
    @app_commands.check(admin_only_check)
    async def disable_collection(self, interaction: discord.Interaction):
        self.collect_active = False
        await interaction.response.send_message("❌ Collection disabled.")

    @app_commands.command(name="collector_status", description="Show current status.")
    async def collector_status(self, interaction: discord.Interaction):
        status = "active ✅" if self.collect_active else "inactive ❌"
        await interaction.response.send_message(f"Collector is currently **{status}**.")

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Admin role required.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Admin role required.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CollectorCog(bot))