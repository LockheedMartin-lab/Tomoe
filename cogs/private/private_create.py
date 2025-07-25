import os
from discord import Object, app_commands
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(dotenv_path="bot.env")

GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]


class Private_Create(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def has_private_owner_role(self, member: discord.Member):
        return any(role.name.startswith("🔑") and role.name.endswith("_owner") for role in member.roles)

    @app_commands.guilds(*[Object(id=gid) for gid in GUILD_IDS])
    @commands.has_permissions(manage_channels=True)
    @app_commands.command(name="private_create", description="Create a private category with role and channels.")
    @app_commands.describe(channelname="The name of your private space")
    async def private_create(self, interaction: discord.Interaction, channelname: str):
        guild = interaction.guild
        author = interaction.user

        if self.has_private_owner_role(author):
            await interaction.response.send_message("❌ You already own a private space.", ephemeral=True)
            return

        name_lower = channelname.lower()
        existing_names = [c.name.lower() for c in list(guild.categories) + list(guild.channels)]
        if name_lower in existing_names:
            await interaction.response.send_message("❌ A category or channel with that name already exists.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)

        # Create roles
        owner_permissions = discord.Permissions()
        owner_permissions.update(
            view_channel=True, connect=True, speak=True,
            mute_members=True, deafen_members=True, move_members=True
        )

        viewer_permissions = discord.Permissions()
        viewer_permissions.update(view_channel=True, connect=True, speak=True)

        role_owner = await guild.create_role(name=f"🔑{channelname}_owner", permissions=owner_permissions)
        role_viewer = await guild.create_role(name=f"🔑{channelname}", permissions=viewer_permissions)
        await author.add_roles(role_owner)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role_owner: discord.PermissionOverwrite(
                view_channel=True, connect=True, speak=True,
                mute_members=True, deafen_members=True, move_members=True
            ),
            role_viewer: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }

        # Create category and channels
        category = await guild.create_category(name=f"🔑{channelname}", overwrites=overwrites)
        await guild.create_text_channel(name=channelname, category=category, overwrites=overwrites)
        await guild.create_voice_channel(name=channelname, category=category, overwrites=overwrites)

        await interaction.followup.send(f"✅ Private space `{channelname}` created!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Private_Create(bot))
