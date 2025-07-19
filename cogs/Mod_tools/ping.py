import discord
from discord.ext import commands
from discord import app_commands
import os

GUILD_IDS = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Replies with pong")
    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

    async def cog_load(self):
        for gid in GUILD_IDS:
            guild = discord.Object(id=gid)
            existing = [cmd.name for cmd in self.bot.tree.get_commands(guild=guild)]
            if "ping" not in existing:
                self.bot.tree.add_command(self.ping, guild=guild)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
