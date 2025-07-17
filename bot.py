import os
import discord
#from discord import app_commands
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
load_dotenv(dotenv_path="bot.env")
TOKEN = os.getenv("BOT_TOKEN")
GUILD_IDS_RAW = os.getenv("GUILD_IDS", "")  # Optional: for fast command updates


# ✅ Parse as list of integers
GUILD_IDS = [int(gid.strip()) for gid in GUILD_IDS_RAW.split(",") if gid.strip()]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Slash command example
@bot.tree.command(name="ping", description="Replies with pong")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")





# On ready: sync commands and load cogs
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Load all cogs in /cogs folder
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")

    # Sync slash commands to all guilds
    for guild_id in GUILD_IDS:
        try:
            await bot.tree.sync(guild=discord.Object(id=guild_id))
            print(f"🔁 Synced slash commands to guild {guild_id}")
        except Exception as e:
            print(f"❌ Failed to sync to guild {guild_id}: {e}")

    
# Run the bot
bot.run(TOKEN)