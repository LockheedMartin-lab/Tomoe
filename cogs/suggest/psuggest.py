import discord
from discord import app_commands
from discord.ext import commands
import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

class PrivateSuggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    def get_suggestion_channel(self, guild_id):
        return self.config.get(str(guild_id), {}).get("suggestion_channel_id")

    @app_commands.command(name="psuggest", description="Submit a private (anonymous) suggestion")
    @app_commands.describe(text="Your suggestion")
    async def psuggest(self, interaction: discord.Interaction, text: str):
        suggestion_channel_id = self.get_suggestion_channel(interaction.guild.id)

        if suggestion_channel_id is None or interaction.channel.id != int(suggestion_channel_id):
            await interaction.response.send_message("❌ Please use this command in the configured suggestions channel.", ephemeral=True)
            return

        embed = discord.Embed(
            title="❓ Anonymous Suggestion",
            description=text,
            color=discord.Color.dark_grey()
        )
        embed.set_footer(text="Anonymous Submission")

        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")

        await interaction.response.send_message("✅ Anonymous suggestion submitted.", ephemeral=True)

    async def cog_load(self):
        """Register command per guild for faster updates."""
        guild_ids = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]
        for gid in guild_ids:
            guild = discord.Object(id=gid)
            self.bot.tree.add_command(self.psuggest, guild=guild)

async def setup(bot):
    await bot.add_cog(PrivateSuggest(bot))
