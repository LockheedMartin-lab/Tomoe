import discord
from discord import app_commands
from discord.ext import commands
import os
import re
from dotenv import load_dotenv

load_dotenv("bot.env")

GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

# Helper function to normalize Discord text channel names
def normalize_discord_channel_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"\s+", "-", name)           # spaces → dashes
    name = re.sub(r"[^a-z0-9\-]", "", name)     # remove non-alphanum/dashes
    name = re.sub(r"-+", "-", name)            # collapse multiple dashes
    return name


class Private_Rename(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    @app_commands.command(name="private_rename", description="Rename your private space")
    @app_commands.describe(current_name="Current name of your private space", new_name="New name for your private space")
    async def private_rename(self, interaction: discord.Interaction, current_name: str, new_name: str):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        author = interaction.user

        normalized_old = normalize_discord_channel_name(current_name)
        normalized_new = normalize_discord_channel_name(new_name)

        expected_owner_role = f"🔑{normalized_old}_owner".lower()
        user_roles = [role.name.lower().replace(" ", "-").strip() for role in author.roles]

        if expected_owner_role not in user_roles and author.id != guild.owner_id:
            await interaction.followup.send("❌ You are not the owner of that space.", ephemeral=True)
            return

        # Match category, text, and voice
        category = discord.utils.find(lambda c: normalize_discord_channel_name(c.name.removeprefix("🔑")) == normalized_old, guild.categories)
        text_channel = discord.utils.find(lambda c: c.name == normalized_old, guild.text_channels)
        voice_channel = discord.utils.find(lambda c: normalize_discord_channel_name(c.name) == normalized_old, guild.voice_channels)

        if not any([category, text_channel, voice_channel]):
            await interaction.followup.send("❌ Could not find the private space.", ephemeral=True)
            return

        # Rename roles
        for role in guild.roles:
            role_name_clean = role.name.lower().removeprefix("🔑").replace(" ", "-").strip()
            if role_name_clean == f"{normalized_old}_owner":
                try:
                    await role.edit(name=f"🔑{new_name}_owner", reason=f"Renamed by {author}")
                except Exception as e:
                    print(f"❌ Failed to rename owner role: {e}")
            elif role_name_clean == normalized_old:
                try:
                    await role.edit(name=f"🔑{new_name}", reason=f"Renamed by {author}")
                except Exception as e:
                    print(f"❌ Failed to rename user role: {e}")

        # Rename text channel (Discord-safe formatting)
        if text_channel:
            try:
                await text_channel.edit(name=normalized_new, reason=f"Renamed by {author}")
            except Exception as e:
                print(f"❌ Failed to rename text channel: {e}")
        
        # Rename voice channel
        if voice_channel:
            try:
                await voice_channel.edit(name=new_name, reason=f"Renamed by {author}")
            except Exception as e:
                print(f"❌ Failed to rename voice channel: {e}")

        # Rename category
        if category:
            try:
                await category.edit(name=f"🔑{new_name}", reason=f"Renamed by {author}")
            except Exception as e:
                print(f"❌ Failed to rename category: {e}")

        await interaction.followup.send(
            f"✅ Renamed private space `{current_name}` to `{new_name}`.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Private_Rename(bot))
