import os
import pathlib
import discord
#from discord import app_commands
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
load_dotenv(dotenv_path="bot.env")
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERID = int(os.getenv("ADMIN_USERID"))
GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")  # Optional: for fast command updates


# ✅ Parse as list of integers
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


#Errorhaneleling permission missing
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You don't have the required permissions to run this command.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ An unexpected error occurred.", ephemeral=True)
        raise error





@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Recursively find and load all cogs from /cogs and its subfolders
    for path in pathlib.Path("cogs").rglob("*.py"):
        if path.name == "__init__.py":
            continue  # Skip __init__.py files
        rel_path = path.with_suffix("")  # remove .py
        module = ".".join(rel_path.parts)

        try:
            await bot.load_extension(module)
            print(f"✅ Loaded cog: {module}")
        except Exception as e:
            print(f"❌ Failed to load cog {module}: {e}")

    # Sync slash commands to all guilds
    for guild_id in GUILD_IDS:
        try:
            await bot.tree.sync(guild=discord.Object(id=guild_id))
            print(f"🔁 Synced slash commands to guild {guild_id}")
        except Exception as e:
            print(f"❌ Failed to sync to guild {guild_id}: {e}")

  
  
# Run the bot
bot.run(TOKEN)