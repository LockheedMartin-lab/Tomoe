import discord
from discord.ext import commands
from discord import app_commands

class DeleteMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge", description="Delete the last X messages in this channel.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(amount="Number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)

        if amount < 1 or amount > 100:
            await interaction.followup.send("❌ Please provide a number between 1 and 100.", ephemeral=True)
            return

        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Deleted {len(deleted)} messages.", ephemeral=True)



async def setup(bot):
    cog = DeleteMessages(bot)
    await bot.add_cog(cog)

    import os
    guild_ids = [int(g.strip()) for g in os.getenv("GUILD_IDS", "").split(",") if g.strip()]

    for gid in guild_ids:
        guild = discord.Object(id=gid)
        existing_commands = [cmd.name for cmd in bot.tree.get_commands(guild=guild)]

        if "purge" not in existing_commands:
            bot.tree.add_command(cog.purge, guild=guild)

    print("✅ DeleteMessages cog loaded")
