# main.py
import os
import asyncio

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admin")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in .env")

# ----- Intents -----
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.members = True

# ----- Bot instance -----
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


# ----- Admin check -----
def has_admin_role(member: discord.Member) -> bool:
    for role in member.roles:
        if role.name == ADMIN_ROLE_NAME:
            return True
    return False


def admin_only_check(interaction: discord.Interaction) -> bool:
    if not isinstance(interaction.user, discord.Member):
        raise app_commands.CheckFailure("Not a guild member.")
    if not has_admin_role(interaction.user):
        raise app_commands.CheckFailure("Missing required admin role.")
    return True


# ----- Events -----
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} application command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")


# ----- Global admin command -----
@bot.tree.command(name="shutdown", description="Shut down the bot (admin only).")
@app_commands.check(admin_only_check)
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down bot...")
    await bot.close()


# ----- Load extensions and start bot -----
async def load_extensions():
    try:
        await bot.load_extension("collector_cog")
        print("Loaded collector_cog.")
    except Exception as e:
        print(f"Failed to load collector_cog: {e}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
