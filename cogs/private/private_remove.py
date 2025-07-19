import os
import discord
import re
from discord.ext import commands
from discord import app_commands, Object
from dotenv import load_dotenv
load_dotenv(dotenv_path="bot.env")

GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

def normalize_channelname(channelname: str) -> str:
    channelname = channelname.strip().replace("!", "")
    channelname = channelname.lower().replace(" ", "-")
    channelname = re.sub(r"[^a-z0-9\-_]", "", channelname)
    return channelname

def normalize_discord_role_channelname(name: str) -> str:
    if name.startswith("🔑"):
        name = name[1:]
    return normalize_channelname(name)

class PrivateRemove(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_owner_of(self, member: discord.Member, channelname: str):
        return any(role.name == f"🔑{channelname}_owner" for role in member.roles)

    @app_commands.guilds(*[Object(id=gid) for gid in GUILD_IDS])
    @commands.has_permissions(manage_channels=True)
    @app_commands.command(name="private_remove", description="Remove a user from your private space.")
    @app_commands.describe(channelname="The name of your private space", user="User to remove")
    async def remove_user(self, interaction: discord.Interaction, channelname: str, user: discord.Member):
        guild = interaction.guild
        author = interaction.user
        channelname_normalized = normalize_channelname(channelname)

        role_owner = discord.utils.find(
            lambda r: normalize_discord_role_channelname(r.name) == f"{channelname_normalized}_owner",
            guild.roles
        )
        role_viewer = discord.utils.find(
            lambda r: normalize_discord_role_channelname(r.name) == channelname_normalized,
            guild.roles
        )

        if not role_owner or not role_viewer:
            await interaction.response.send_message("❌ That private space does not exist.", ephemeral=True)
            return

        if role_owner not in author.roles:
            await interaction.response.send_message("❌ You are not the owner of that space.", ephemeral=True)
            return

        await user.remove_roles(role_viewer)
        await interaction.response.send_message(f"✅ {user.mention} removed from `{channelname}`!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PrivateRemove(bot))
