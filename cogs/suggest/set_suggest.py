# cogs/suggest/set_suggest.py

import discord
from discord import app_commands
from discord.ext import commands
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

class SetSuggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="set_suggestion_channel", 
        description="Set the suggestion channel for this server")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="The channel to use for suggestions")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}

        self.config[guild_id]["suggestion_channel_id"] = channel.id
        save_config(self.config)

        await interaction.response.send_message(f"✅ Suggestion channel set to {channel.mention}", ephemeral=True)

    async def cog_load(self):
        guild_ids = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]
        for gid in guild_ids:
            self.bot.tree.add_command(self.set_channel, guild=discord.Object(id=gid))

async def setup(bot):
    await bot.add_cog(SetSuggest(bot))
