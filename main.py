import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive
import asyncio
from datetime import datetime, timedelta
import pytz

# Initialize bot and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
event_data = {}
THAI_TZ = pytz.timezone("Asia/Bangkok")

#=============================================================================================
# Helper function to format user names
def format_names(user_ids, guild):
    """Format user names for display."""
    if not user_ids:
        return "- ไม่มี -"
    names = []
    for uid in user_ids:
        member = guild.get_member(uid)
        if member:
            names.append(f"- {member.display_name}")
    return "\n".join(names)

#=============================================================================================
# EventJoinView class for handling event responses
class EventJoinView(discord.ui.View):
    def __init__(self, title, event_time):
        super().__init__(timeout=None)
        self.title = title
        self.event_time = event_time

    async def handle_response(self, interaction: discord.Interaction, status: str, button: discord.ui.Button):
        message_id = interaction.message.id
        user_id = interaction.user.id

        if message_id not in event_data:
            await interaction.response.send_message("❌ ไม่พบข้อมูลกิจกรรม", ephemeral=True)
            return

        # Remove old status if exists
        for s in ["going", "maybe", "declined"]:
            if user_id in event_data[message_id][s]:
                event_data[message_id][s].remove(user_id)

        # Add new status
        event_data[message_id][status].append(user_id)

        # Update embed
        if not interaction.message.embeds:
            await interaction.response.send_message("❌ ไม่พบ embed ของกิจกรรมนี้", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.set_field_at(
            4,
            name="📋 การเข้าร่วม",
            value=(
                f"👍 เข้าร่วม: {len(event_data[message_id]['going'])}\n"
                f"❔ อาจจะมา: {len(event_data[message_id]['maybe'])}\n"
                f"❌ ไม่มา: {len(event_data[message_id]['declined'])}"
            ),
            inline=False
        )

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"📌 คุณตอบว่า: {button.label}", ephemeral=True)

    # Buttons for event responses
    @discord.ui.button(label="✅ มาแน่นอน", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "going", button)

    @discord.ui.button(label="❔ อาจจะมา", style=discord.ButtonStyle.primary)
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "maybe", button)

    @discord.ui.button(label="❌ ไม่มา", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "declined", button)

#=============================================================================================
# Command to create a new event
@bot.tree.command(name="event", description="สร้างอีเวนต์ใหม่")
@app_commands.describe(
    title="หัวข้ออีเวนต์",
    editor_info="Editor by / Preset / Mod",
    story="เนื้อเรื่องของภารกิจ",
    roles="บทบาทที่รับ (เช่น Rifleman, Sniper)",
    time="เวลา (เช่น 11-04-2025 18:30)",
    channel="ห้องที่ต้องการโพสต์อีเวนต์",
    image_url="ลิงก์รูปภาพ (ไม่บังคับ)"
)
async def create_event(
    interaction: discord.Interaction,
    title: str,
    editor_info: str,
    story: str,
    roles: str,
    time: str,
    channel: discord.TextChannel,
    image_url: str = None
):
    try:
        event_time = datetime.strptime(time, "%d-%m-%Y %H:%M")
        event_time = THAI_TZ.localize(event_time).astimezone(pytz.utc)
    except ValueError:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง! ใช้รูปแบบ: DD-MM-YYYY HH:MM", ephemeral=True)
        return

    embed = discord.Embed(title=title, color=discord.Color.green())
    embed.add_field(name="🛠️ Editor / Preset / Mod", value=editor_info, inline=False)
    embed.add_field(name="📖 Story", value=story, inline=False)
    embed.add_field(name="🎭 Roles", value=roles, inline=False)
    embed.add_field(name="🕒 วันและเวลา", value=event_time.astimezone(THAI_TZ).strftime("%d-%m-%Y %H:%M น."), inline=False)
    embed.add_field(name="📋 การเข้าร่วม", value="👍 เข้าร่วม: 0\n❔ อาจจะมา: 0\n❌ ไม่มา: 0", inline=False)

    if image_url:
        embed.set_image(url=image_url)

    view = EventJoinView(title, event_time)
    msg = await channel.send(embed=embed, view=view)

    thread = await msg.create_thread(name=f"🗓️ {title}", auto_archive_duration=60)
    await thread.send(f"📢 กิจกรรม `{title}` ถูกสร้างโดย <@{interaction.user.id}>")

    event_data[msg.id] = {
        "title": title,
        "event_time": event_time,
        "going": [],
        "maybe": [],
        "declined": [],
        "thread_id": thread.id,
        "message_id": msg.id,
        "channel_id": channel.id
    }

    await interaction.response.send_message("✅ กิจกรรมถูกสร้างเรียบร้อยแล้ว!", ephemeral=True)

#=============================================================================================
# Add other commands and events as needed...
#=============================================================================================

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
