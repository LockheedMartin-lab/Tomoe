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


# Slash command example
@bot.tree.command(name="ping", description="Replies with pong")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")


#Errorhaneleling permission missing
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You don't have the required permissions to run this command.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ An unexpected error occurred.", ephemeral=True)
        raise error


#sync -> fixes commands
@app_commands.default_permissions(administrator=True)
@app_commands.command(name="sync",description="Force sync commands")
@app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
async def sync(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_USERID:
        await interaction.response.send_message("❌ You are not allowed to use this.", ephemeral=True)
        return

    # ⏳ Acknowledge the command before doing the slow sync
    await interaction.response.defer(thinking=True, ephemeral=True)

    synced = 0
    for guild_id in GUILD_IDS:
        try:
            await bot.tree.sync(guild=discord.Object(id=guild_id))
            synced += 1
        except Exception as e:
            print(f"❌ Failed to sync to guild {guild_id}: {e}")

    await interaction.followup.send(f"✅ Synced commands to {synced} guild(s)", ephemeral=True)
# Register the command explicitly
bot.tree.add_command(sync)



#Listcommands -> lists all current commands
@app_commands.default_permissions(administrator=True)
@app_commands.command(name="listcommands", description="List all registered commands")
@app_commands.guilds(*[discord.Object(id=gid) for gid in GUILD_IDS])
async def listcommands(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_USERID:
        await interaction.response.send_message("❌ You are not allowed to use this.", ephemeral=True)
        return

    commands = bot.tree.get_commands()
    if not commands:
        await interaction.response.send_message("ℹ️ No commands are currently registered.", ephemeral=True)
        return

    output = "\n".join(f"- `{cmd.name}`: {cmd.description}" for cmd in commands)
    await interaction.response.send_message(f"📜 **Registered Commands:**\n{output}", ephemeral=True)
# Register the command explicitly
bot.tree.add_command(listcommands)





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