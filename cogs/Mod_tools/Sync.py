import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
load_dotenv(dotenv_path="bot.env")

# Load environment variables
GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
ADMIN_USERID = int(os.getenv("ADMIN_USERID", "0"))
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

class SyncCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    @app_commands.command(name="sync", description="Force sync commands")
    async def sync(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_USERID:
            await interaction.response.send_message("❌ You are not allowed to use this.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True, ephemeral=True)

        synced = 0
        for guild_id in GUILD_IDS:
            try:
                await self.bot.tree.sync(guild=discord.Object(id=guild_id))
                synced += 1
            except Exception as e:
                print(f"❌ Failed to sync to guild {guild_id}: {e}")

        await interaction.followup.send(f"✅ Synced commands to {synced} guild(s)", ephemeral=True)

# Setup function for loading the cog
async def setup(bot: commands.Bot):
    await bot.add_cog(SyncCommands(bot))
