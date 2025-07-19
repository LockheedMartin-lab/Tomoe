import discord
from discord.ext import commands
from discord import app_commands
import os
import json  
from asyncio import sleep

TICKET_CATEGORY_NAME = "🙋support"
TICKET_CHANNEL_NAME = "🙋support"
TICKET_PREFIX = "ticket-"

TICKET_PATH = os.path.join(os.path.dirname(__file__), "ticket.json")

# Load/save helpers
def load_ticket_data():
    if not os.path.exists(TICKET_PATH):
        return {}
    with open(TICKET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_ticket_data(data):
    with open(TICKET_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)
        await sleep(7)
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    def load_ticket_count(self, guild_id: int) -> int:
        data = load_ticket_data()
        return data.get(str(guild_id), {}).get("ticket_count", 0)

    def save_ticket_count(self, guild_id: int, count: int):
        data = load_ticket_data()
        guild_key = str(guild_id)
        if guild_key not in data:
            data[guild_key] = {}
        data[guild_key]["ticket_count"] = count
        save_ticket_data(data)
        # print(f"[Ticket] Saved ticket count {count} for guild {guild_key}") # <-for debugging if number doesn't work

    @discord.ui.button(label="Create ticket", emoji="📩", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        author = interaction.user

        # Load and increment ticket count
        ticket_count = self.load_ticket_count(guild.id) + 1
        self.save_ticket_count(guild.id, ticket_count)
        channel_name = f"{TICKET_PREFIX}{ticket_count:04d}"

        # Get or create the support category
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            return await interaction.response.send_message("❌ Support category not found.", ephemeral=True)

        # Set up permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True)

        # Create the ticket channel
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        # Confirm to user
        await interaction.response.send_message(
            f"✅ Ticket created in {ticket_channel.mention}", ephemeral=True
        )

        # Welcome embed
        embed = discord.Embed(
            description=(
                f"🇺🇸 {author.mention} Welcome, the moderators are going to get in touch with you as soon as possible.\n"
                f"🇩🇪 {author.mention} Willkommen, die Moderation wird mit dir hier schnellstmöglich in Kontakt treten.\n\n"
                "*Please wait patiently while your request is being processed.*"
            ),
            color=discord.Color.blurple()
        )

        await ticket_channel.send(embed=embed, view=CloseTicketView())


class TicketSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_view = TicketView(bot)

    @app_commands.command(name="setup_ticket", description="Setup a support channel with a ticket button.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild

        # Create category if missing
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        # Create support channel if missing
        support_channel = discord.utils.get(category.channels, name=TICKET_CHANNEL_NAME)
        if not support_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)
            }
            support_channel = await guild.create_text_channel(TICKET_CHANNEL_NAME, category=category, overwrites=overwrites)

        # Embed
        embed = discord.Embed(
            title=f"{guild.name} Support",
            description=(
                ":flag_us: To get in touch with the moderation, click 📩 below this message\n\n"
                ":flag_de: Um mit der Moderation in Kontakt zu treten, klicke auf 📩 unter dieser Nachricht\n"
            ),
            color=discord.Color.green()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await support_channel.send(embed=embed, view=self.ticket_view)
        await interaction.response.send_message(f"✅ Ticket support system initialized in {support_channel.mention}", ephemeral=True)

    async def cog_load(self):
        self.bot.add_view(self.ticket_view)
        self.bot.add_view(CloseTicketView())

        # Per-guild registration (for dev/test)
        guild_ids = [int(gid) for gid in os.getenv("GUILD_IDS", "").split(",") if gid]
        for gid in guild_ids:
            self.bot.tree.add_command(self.setup_ticket, guild=discord.Object(id=gid))


async def setup(bot):
    await bot.add_cog(TicketSetup(bot))
