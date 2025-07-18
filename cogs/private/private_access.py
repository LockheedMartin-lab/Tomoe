import os
import discord
from discord.ext import commands
from discord import app_commands
from discord import Object, app_commands
from dotenv import load_dotenv
load_dotenv(dotenv_path="bot.env")

GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]


class PrivateAccess(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_owner_of(self, member: discord.Member, name: str):
        return any(role.name == f"🔑{name}_owner" for role in member.roles)

    @app_commands.guilds(*[Object(id=gid) for gid in GUILD_IDS])
    @commands.has_permissions(manage_channels=True)
    @app_commands.command(name="add", description="Add a user to your private space.")
    async def add_user(self, interaction: discord.Interaction, name: str, user: discord.Member):
        guild = interaction.guild
        author = interaction.user

        role_owner = discord.utils.get(guild.roles, name=f"🔑{name}_owner")
        role_viewer = discord.utils.get(guild.roles, name=f"🔑{name}")

        if not role_owner or not role_viewer:
            await interaction.response.send_message("❌ That private space does not exist.", ephemeral=True)
            return

        if role_owner not in author.roles:
            await interaction.response.send_message("❌ You are not the owner of that space.", ephemeral=True)
            return

        await user.add_roles(role_viewer)
        await interaction.response.send_message(f"✅ {user.mention} added to `{name}`!", ephemeral=True)

    
    @app_commands.guilds(*[Object(id=gid) for gid in GUILD_IDS])
    @commands.has_permissions(manage_channels=True)
    @app_commands.command(name="remove", description="Remove a user from your private space.")
    async def remove_user(self, interaction: discord.Interaction, name: str, user: discord.Member):
        guild = interaction.guild
        author = interaction.user

        role_owner = discord.utils.get(guild.roles, name=f"🔑{name}_owner")
        role_viewer = discord.utils.get(guild.roles, name=f"🔑{name}")

        if not role_owner or not role_viewer:
            await interaction.response.send_message("❌ That private space does not exist.", ephemeral=True)
            return

        if role_owner not in author.roles:
            await interaction.response.send_message("❌ You are not the owner of that space.", ephemeral=True)
            return

        await user.remove_roles(role_viewer)
        await interaction.response.send_message(f"✅ {user.mention} removed from `{name}`!", ephemeral=True)

# ✅ Setup
async def setup(bot: commands.Bot):
    cog = PrivateAccess(bot)
    await bot.add_cog(cog)
