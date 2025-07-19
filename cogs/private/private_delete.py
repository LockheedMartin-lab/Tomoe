import os
import re
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv(dotenv_path="bot.env")

GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

# --- Helpers ---

def normalize_name(name: str) -> str:
    """Normalize user input for consistent channel/role matching."""
    name = name.strip().replace("!", "")
    name = name.lower().replace(" ", "-")
    name = re.sub(r"[^a-z0-9\-_]", "", name)
    return name

def normalize_discord_role_name(name: str) -> str:
    """Normalize an actual Discord role name (e.g., remove emoji prefix)."""
    if name.startswith("🔑"):
        name = name[1:]
    return normalize_name(name)

# --- View for deletion confirmation ---

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


# --- Main Cog ---

class Private_DeleteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
    @app_commands.command(name="private_delete", description="Request deletion of a private space.")
    @app_commands.describe(channel_name="Name of your private space to delete (base name only)")
    async def delete_space(self, interaction: discord.Interaction, channel_name: str):
        guild = interaction.guild
        author = interaction.user
        normalized_name = normalize_name(channel_name)

        # Find the category and channels
        category = discord.utils.find(lambda c: normalize_name(c.name.removeprefix("🔑")) == normalized_name, guild.categories)
        text_channel = discord.utils.find(lambda c: normalize_name(c.name) == normalized_name, guild.text_channels)
        voice_channel = discord.utils.find(lambda c: normalize_name(c.name) == normalized_name, guild.voice_channels)

        if not category and not text_channel and not voice_channel:
            await interaction.response.send_message(f"❌ Could not find a private space named `{channel_name}`.", ephemeral=True)
            return

        # Check permissions
        any_channel = category or text_channel or voice_channel
        if not any_channel.permissions_for(author).manage_channels and author.id != guild.owner_id:
            await interaction.response.send_message("❌ You don't have permission to delete this space.", ephemeral=True)
            return

        # Deletion logic
        async def delete_everything():
            deleted_items = {}

            # Delete channels
            for item, label in [(text_channel, "Text-Channel"), (voice_channel, "Voice-Channel"), (category, "Category")]:
                if item:
                    try:
                        await item.delete(reason=f"Deleted by {author} via /delete")
                        deleted_items[label] = item.name
                    except Exception as e:
                        print(f"❌ Failed to delete {label}: {e}")

            # Delete roles
            for role in guild.roles:
                role_clean = normalize_discord_role_name(role.name)
                if role_clean == f"{normalized_name}_owner":
                    try:
                        await role.delete(reason=f"Deleted by {author} via /delete")
                        deleted_items["Owner-Role"] = role.name
                    except Exception as e:
                        print(f"❌ Failed to delete owner role: {e}")
                elif role_clean == normalized_name:
                    try:
                        await role.delete(reason=f"Deleted by {author} via /delete")
                        deleted_items["User-Role"] = role.name
                    except Exception as e:
                        print(f"❌ Failed to delete user role: {e}")

            if deleted_items:
                formatted = "\n".join(f"{key}: `{value}`" for key, value in deleted_items.items())
                try:
                    await interaction.followup.send(
                        f"✅ Deleted the private space `{channel_name}` and associated resources:\n{formatted}",
                        ephemeral=True
                    )
                except discord.NotFound:
                    try:
                        await interaction.user.send(
                            f"✅ Your private space `{channel_name}` was deleted, but the original channel was already gone."
                        )
                    except Exception:
                        pass

                
            else:
                await interaction.followup.send("⚠️ Nothing was deleted.", ephemeral=True)

        # Ask for confirmation
        view = ConfirmDeleteView(author.id, delete_callback=delete_everything)
        await interaction.response.send_message(
            f"⚠️ Confirm deletion of your private space `{channel_name}` within 20 seconds.",
            view=view,
            ephemeral=True
        )
        view.message = await interaction.original_response()


# --- Setup ---
async def setup(bot: commands.Bot):
    await bot.add_cog(Private_DeleteCog(bot))
