import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
load_dotenv(dotenv_path="bot.env")

# Load env variables
GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
ADMIN_USERID = int(os.getenv("ADMIN_USERID", "0"))
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

class ListCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    @app_commands.command(name="listcommands", description="List all registered commands")
    async def listcommands(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_USERID:
            await interaction.response.send_message("❌ You are not allowed to use this.", ephemeral=True)
            return

        # Fetch guild-specific commands
        guild_commands = await self.bot.tree.fetch_commands(guild=interaction.guild)

        if not guild_commands:
            await interaction.response.send_message("ℹ️ No commands are currently registered.", ephemeral=True)
            return

        output = "\n".join(f"- `{cmd.name}`: {cmd.description}" for cmd in guild_commands)
        await interaction.response.send_message(f"📜 **Registered Commands for this Guild:**\n{output}", ephemeral=True)

# Setup function for loading the cog
async def setup(bot: commands.Bot):
    await bot.add_cog(ListCommands(bot))
