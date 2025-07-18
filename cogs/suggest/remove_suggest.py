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

class RemoveSuggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    def get_suggestion_channel(self, guild_id):
        return self.config.get(str(guild_id), {}).get("suggestion_channel_id")

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="remove_suggestion_channel", 
        description="Remove the configured suggestion channel for this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_channel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild = interaction.guild
        channel_id = self.get_suggestion_channel(guild.id)

        if not channel_id:
            await interaction.response.send_message("ℹ️ No suggestion channel is currently set for this server.", ephemeral=True)
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("⚠️ The configured suggestion channel could not be found.", ephemeral=True)
            return

        # Remove it from config
        del self.config[guild_id]["suggestion_channel_id"]
        if not self.config[guild_id]:  # Remove empty dict
            del self.config[guild_id]
        save_config(self.config)

        await interaction.response.send_message(f"✅ Removed suggestion channel: {channel.mention}", ephemeral=True)

    async def cog_load(self):
        """Register this command per-guild"""
        guild_ids = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]
        for gid in guild_ids:
            self.bot.tree.add_command(self.remove_channel, guild=discord.Object(id=gid))

async def setup(bot):
    await bot.add_cog(RemoveSuggest(bot))