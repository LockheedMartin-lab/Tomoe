import discord
from discord.ext import commands
from discord import app_commands
import os


class Private(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Slash command itself
    async def privatecreate(self, interaction: discord.Interaction, name: str):
        guild = interaction.guild
        author = interaction.user

        await interaction.response.defer(thinking=True)

         # Owner role permissions (admin-like)
        owner_permissions = discord.Permissions()
        owner_permissions.update(
            view_channel=True,
            connect=True,
            speak=True,
            mute_members=True,
            deafen_members=True,
            move_members=True
        )

        # Viewer role permissions (basic view/connect/speak)
        viewer_permissions = discord.Permissions()
        viewer_permissions.update(
            view_channel=True,
            connect=True,
            speak=True
        )

        # Create roles
        role_owner = await guild.create_role(name=f"🔑{name}_owner", permissions=owner_permissions, reason="Private space owner role")
        role_viewer = await guild.create_role(name=f"🔑{name}", permissions=viewer_permissions, reason="Private space viewer role")

        # Assign owner role to the author
        await author.add_roles(role_owner)

        # Build overwrites with both roles included
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role_owner: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                mute_members=True,
                deafen_members=True,
                move_members=True,
            ),
            role_viewer: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
            ),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }


        category = await guild.create_category(name=name, overwrites=overwrites)
        await guild.create_text_channel(name=name, category=category, overwrites=overwrites)
        await guild.create_voice_channel(name=name, category=category, overwrites=overwrites)

        await interaction.followup.send(f"✅ Private space `{name}` created!", ephemeral=True)

# ✅ Required setup function
async def setup(bot: commands.Bot):
    cog = Private(bot)
    await bot.add_cog(cog)

    # ✅ Manually register the command as slash
    command = app_commands.Command(
        name="privatecreate",
        description="Create a private category with role and channels.",
        callback=cog.privatecreate
    )

    # ✅ Register in each guild from env
    guild_ids = [int(gid.strip()) for gid in os.getenv("GUILD_IDS", "").split(",") if gid.strip()]
    for gid in guild_ids:
        bot.tree.add_command(command, guild=discord.Object(id=gid))

