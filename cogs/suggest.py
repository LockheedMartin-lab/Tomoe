import discord
from discord import app_commands
from discord.ext import commands
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class SuggestionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    def get_suggestion_channel(self, guild_id):
        return self.config.get(str(guild_id), {}).get("suggestion_channel_id")

    @app_commands.command(name="set_suggestion_channel", description="Set the suggestion channel for this server")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="The channel to use for suggestions")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}

        self.config[guild_id]["suggestion_channel_id"] = channel.id
        save_config(self.config)

        await interaction.response.send_message(f"✅ Suggestion channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="suggest", description="Submit a public suggestion")
    @app_commands.describe(text="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, text: str):
        suggestion_channel_id = self.get_suggestion_channel(interaction.guild.id)

        if suggestion_channel_id is None or interaction.channel.id != suggestion_channel_id:
            await interaction.response.send_message("❌ Please use this command in the configured suggestions channel.", ephemeral=True)
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

    @app_commands.command(name="psuggest", description="Submit a private (anonymous) suggestion")
    @app_commands.describe(text="Your suggestion")
    async def psuggest(self, interaction: discord.Interaction, text: str):
        suggestion_channel_id = self.get_suggestion_channel(interaction.guild.id)

        if suggestion_channel_id is None or interaction.channel.id != suggestion_channel_id:
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
        """Register all commands per-guild for faster updates."""
        guild_ids = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]
        for gid in guild_ids:
            guild = discord.Object(id=gid)
            self.bot.tree.add_command(self.set_channel, guild=guild)
            self.bot.tree.add_command(self.suggest, guild=guild)
            self.bot.tree.add_command(self.psuggest, guild=guild)

# ✅ Setup function called by discord.py when loading this cog
async def setup(bot):
    await bot.add_cog(SuggestionCog(bot))
