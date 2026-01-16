"""
Admin permission checks for Discord bot commands.
"""

import os
from discord import app_commands
from discord.ext import commands
import discord
from dotenv import load_dotenv

load_dotenv()

ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "Admin")


def has_admin_role(member: discord.Member) -> bool:
    """Check if a member has the admin role."""
    for role in member.roles:
        if role.name == ADMIN_ROLE_NAME:
            return True
    return False


def admin_only_check(interaction: discord.Interaction) -> bool:
    """Check that ensures only admin members can run a command."""
    if not isinstance(interaction.user, discord.Member):
        raise app_commands.CheckFailure("Not a guild member.")
    if not has_admin_role(interaction.user):
        raise app_commands.CheckFailure("Missing required admin role.")
    return True
