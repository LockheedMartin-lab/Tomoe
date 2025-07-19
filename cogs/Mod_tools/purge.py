import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
load_dotenv(dotenv_path="bot.env")

GUILD_IDS = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]

class DeleteMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    @app_commands.command(name="purge", description="Delete the last X messages in this channel.")
    @app_commands.describe(amount="Number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)

        if amount < 1 or amount > 100:
            await interaction.followup.send("❌ Please provide a number between 1 and 100.", ephemeral=True)
            return

        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Deleted {len(deleted)} messages.", ephemeral=True)

# Standard setup function for loading this cog
async def setup(bot: commands.Bot):
    await bot.add_cog(DeleteMessages(bot))
