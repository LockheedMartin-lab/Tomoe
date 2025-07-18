import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# Path to the config file in the same folder
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    def get_suggestion_channel(self, guild_id):
        return self.config.get(str(guild_id), {}).get("suggestion_channel_id")

    @app_commands.command(name="suggest", description="Submit a public suggestion")
    @app_commands.describe(text="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, text: str):
        suggestion_channel_id = self.get_suggestion_channel(interaction.guild.id)

        if suggestion_channel_id is None or interaction.channel.id != int(suggestion_channel_id):
            await interaction.response.send_message(
                "❌ Please use this command in the configured suggestions channel.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📣 Suggestion",
            description=text,
            color=discord.Color.blue()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"User ID: {interaction.user.id}")

        msg = await interaction.channel.send(content=interaction.user.mention, embed=embed)
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")

        await interaction.response.send_message("✅ Suggestion submitted.", ephemeral=True)

    async def cog_load(self):
        """Register this command per-guild for faster sync"""
        guild_ids = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]
        for gid in guild_ids:
            self.bot.tree.add_command(self.suggest, guild=discord.Object(id=gid))

async def setup(bot):
    await bot.add_cog(Suggest(bot))
