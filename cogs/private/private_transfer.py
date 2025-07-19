import discord
from discord import app_commands
from discord.ext import commands
import os
import re
from dotenv import load_dotenv

load_dotenv("bot.env")

GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

def normalize_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^a-z0-9\-]", "", name)
    name = re.sub(r"-+", "-", name)
    return name

class Private_Transfer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    @app_commands.command(name="private_transfer", description="Transfer ownership of your private space to another user")
    @app_commands.describe(current_name="Current name of your private space", new_owner="The user who should become the new owner")
    async def private_transfer(self, interaction: discord.Interaction, current_name: str, new_owner: discord.Member):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        original_owner = interaction.user
        normalized = normalize_name(current_name)

        expected_owner_role_name = f"🔑{normalized}_owner"
        expected_viewer_role_name = f"🔑{normalized}"

        owner_role = discord.utils.get(guild.roles, name=expected_owner_role_name)
        viewer_role = discord.utils.get(guild.roles, name=expected_viewer_role_name)

        if not owner_role or not viewer_role:
            await interaction.followup.send("❌ Could not find the roles for that space.", ephemeral=True)
            return

        if owner_role not in original_owner.roles and original_owner.id != guild.owner_id:
            await interaction.followup.send("❌ You are not the owner of that space.", ephemeral=True)
            return

        if new_owner == original_owner:
            await interaction.followup.send("❌ You are already the owner.", ephemeral=True)
            return

        try:
            # Transfer roles
            await original_owner.remove_roles(owner_role, reason="Transferred ownership")
            await original_owner.add_roles(viewer_role, reason="Became viewer after transfer")
            await new_owner.add_roles(owner_role, reason="Received ownership via transfer")

            await interaction.followup.send(
                f"✅ Ownership of `{current_name}` transferred to {new_owner.mention}.",
                ephemeral=True
            )
        except Exception as e:
            print(f"❌ Failed to transfer ownership: {e}")
            await interaction.followup.send("❌ Something went wrong during the transfer.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Private_Transfer(bot))
