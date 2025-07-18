import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv(dotenv_path="bot.env")

GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, author_id: int, delete_callback):
        super().__init__(timeout=20)
        self.author_id = author_id
        self.delete_callback = delete_callback
        self.confirmed = False
        self.message = None

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ You cannot confirm this deletion.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=False)
        await self.delete_callback()
        self.confirmed = True
        self.stop()

    async def on_timeout(self):
        if not self.confirmed and self.message:
            try:
                await self.message.edit(content="⌛ Deletion timed out.", view=None)
            except discord.NotFound:
                pass


class PrivateDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    @app_commands.command(name="delete", description="Request deletion of a private space.")
    @app_commands.describe(channel_name="Name of your private space to delete (base name only)")
    async def delete_space(self, interaction: discord.Interaction, channel_name: str):
        guild = interaction.guild
        author = interaction.user
        name_lower = channel_name.lower()

        # Find the category and channels
        category = discord.utils.get(guild.categories, name=channel_name)
        text_channel = discord.utils.get(guild.text_channels, name=channel_name)
        voice_channel = discord.utils.get(guild.voice_channels, name=channel_name)

        if not category and not text_channel and not voice_channel:
            await interaction.response.send_message(f"❌ Could not find a private space named `{channel_name}`.", ephemeral=True)
            return

        # Check permissions
        any_channel = category or text_channel or voice_channel
        if not any_channel.permissions_for(author).manage_channels and author.id != guild.owner_id:
            await interaction.response.send_message("❌ You don't have permission to delete this space.", ephemeral=True)
            return

        # Define deletion logic
        async def delete_everything():
            deleted_items = {}

            # Text channel
            if text_channel:
                try:
                    await text_channel.delete(reason=f"Deleted by {author} via /delete")
                    deleted_items["Text-Channel"] = text_channel.name
                except Exception as e:
                    print(f"❌ Failed to delete text channel: {e}")

            # Voice channel
            if voice_channel:
                try:
                    await voice_channel.delete(reason=f"Deleted by {author} via /delete")
                    deleted_items["Voice-Channel"] = voice_channel.name
                except Exception as e:
                    print(f"❌ Failed to delete voice channel: {e}")

            # Category
            if category:
                try:
                    await category.delete(reason=f"Deleted by {author} via /delete")
                    deleted_items["Category"] = category.name
                except Exception as e:
                    print(f"❌ Failed to delete category: {e}")

            # Roles
            for role in guild.roles:
                if role.name.lower() == f"🔑{name_lower}_owner":
                    try:
                        await role.delete(reason=f"Deleted by {author} via /delete")
                        deleted_items["Owner-Role"] = role.name
                    except Exception as e:
                        print(f"❌ Failed to delete owner role: {e}")
                elif role.name.lower() == f"🔑{name_lower}":
                    try:
                        await role.delete(reason=f"Deleted by {author} via /delete")
                        deleted_items["User-Role"] = role.name
                    except Exception as e:
                        print(f"❌ Failed to delete user role: {e}")

            if deleted_items:
                formatted = "\n".join(f"{key}: `{value}`" for key, value in deleted_items.items())
                await interaction.followup.send(
                    f"✅ Deleted the private space `{channel_name}` and associated resources:\n{formatted}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("⚠️ Nothing was deleted.", ephemeral=True)

        # Ask user for confirmation
        view = ConfirmDeleteView(author.id, delete_callback=delete_everything)
        await interaction.response.send_message(
            f"⚠️ Confirm deletion of your private space `{channel_name}` within 20 seconds.",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(PrivateDelete(bot))
