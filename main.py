import discord
from discord.ext import commands
from discord import app_commands
import os
import openai
from keep_alive import keep_alive
import asyncio
from datetime import datetime, timedelta
import pytz


# ตั้งค่า intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# สร้างบอท
bot = commands.Bot(command_prefix='!', intents=intents)

# ตั้งค่า OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# ข้อมูลอีเวนต์ทั้งหมด
event_data = {}

# Timezone ของไทย
THAI_TZ = pytz.timezone("Asia/Bangkok")

# คลาสสำหรับการเลือกห้อง
class ChannelSelect(discord.ui.Select):
    def __init__(self):
        options = []
        # ดึงห้องทั้งหมดในเซิร์ฟเวอร์ที่สามารถโพสต์ได้
        for channel in interaction.guild.text_channels:
            options.append(discord.SelectOption(label=channel.name, value=str(channel.id)))

        super().__init__(placeholder="เลือกห้องที่ต้องการโพสต์กิจกรรม", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # กำหนดให้กิจกรรมจะโพสต์ในช่องที่เลือก
        selected_channel = interaction.guild.get_channel(int(self.values[0]))
        await selected_channel.send(f"**กิจกรรมใหม่**: {self.event_data['title']}")

        # ส่งข้อความตอบกลับ
        await interaction.response.send_message(f"กิจกรรมจะถูกโพสต์ในช่อง: {selected_channel.mention}", ephemeral=True)


class EventView(discord.ui.View):
    def __init__(self, event_id):
        super().__init__(timeout=None)
        self.event_id = event_id

    @discord.ui.button(label="✅ มาแน่นอน", style=discord.ButtonStyle.green)
    async def going(self, interaction: discord.Interaction, button: discord.ui.Button):
        clear_user_from_all(self.event_id, interaction.user)
        event_data[self.event_id]["going"].add(interaction.user)
        await self.update_message(interaction)

    @discord.ui.button(label="❓ อาจจะมา", style=discord.ButtonStyle.gray)
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        clear_user_from_all(self.event_id, interaction.user)
        event_data[self.event_id]["maybe"].add(interaction.user)
        await self.update_message(interaction)

    @discord.ui.button(label="❌ ไม่มา", style=discord.ButtonStyle.red)
    async def not_going(self, interaction: discord.Interaction, button: discord.ui.Button):
        clear_user_from_all(self.event_id, interaction.user)
        event_data[self.event_id]["not_going"].add(interaction.user)
        await self.update_message(interaction)

    @discord.ui.button(label="📝 Edit", style=discord.ButtonStyle.blurple, row=1)
    async def edit_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛠 ฟีเจอร์แก้ไขกำลังพัฒนา", ephemeral=True)

    @discord.ui.button(label="🗑 Delete", style=discord.ButtonStyle.red, row=1)
    async def delete_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == event_data[self.event_id]["creator"]:
            del event_data[self.event_id]
            await interaction.message.delete()
        else:
            await interaction.response.send_message("❌ คุณไม่ใช่ผู้สร้างกิจกรรมนี้", ephemeral=True)

    async def update_message(self, interaction):
        embed = generate_event_embed(self.event_id)
        await interaction.response.edit_message(embed=embed, view=self)

def clear_user_from_all(event_id, user):
    for group in ["going", "maybe", "not_going"]:
        event_data[event_id][group].discard(user)

def generate_event_embed(event_id):
    data = event_data[event_id]
    local_time = data['time'].astimezone(THAI_TZ)
    embed = discord.Embed(
        title=f"📌 Operation: {data['title']}",
        description=data["description"],
        color=discord.Color.dark_purple()
    )
    embed.add_field(name=f"✅ Accepted ({len(data['going'])})",
                    value="\n".join(user.display_name for user in data["going"]) or "ไม่มี", inline=True)
    embed.add_field(name=f"❌ Declined ({len(data['not_going'])})",
                    value="\n".join(user.display_name for user in data["not_going"]) or "ไม่มี", inline=True)
    embed.add_field(name=f"❓ Tentative ({len(data['maybe'])})",
                    value="\n".join(user.display_name for user in data["maybe"]) or "ไม่มี", inline=True)
    embed.add_field(name="🕒 Time",
                    value=f"{local_time.strftime('%d-%m-%Y %H:%M')} น. [เพิ่มใน Google](https://calendar.google.com/calendar/render?action=TEMPLATE&text={data['title'].replace(' ', '+')}&dates={data['time'].strftime('%Y%m%dT%H%M00')}/{(data['time'] + timedelta(hours=2)).strftime('%Y%m%dT%H%M00')})",
                    inline=False)
    if "image_url" in data:
        embed.set_image(url=data["image_url"])
    embed.set_footer(text=f"Created by {data['creator'].display_name}")
    return embed

class ConfirmEventView(discord.ui.View):
    def __init__(self, title, description, event_time, image_url, user):
        super().__init__(timeout=60)
        self.title = title
        self.description = description
        self.event_time = event_time
        self.image_url = image_url
        self.user = user

        # เพิ่มช่องเลือกห้องในหน้าต่าง Confirm
        self.channel_select = ChannelSelect()
        self.add_item(self.channel_select)

    @discord.ui.button(label="✅ ยืนยันสร้างกิจกรรม", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ เฉพาะผู้สร้างเท่านั้นที่สามารถยืนยันได้", ephemeral=True)
            return

        # เพิ่มการโพสต์กิจกรรมในห้องที่เลือก
        selected_channel = interaction.guild.get_channel(int(self.channel_select.values[0]))
        event_id = len(event_data)
        event_data[event_id] = {
            "title": self.title,
            "description": self.description,
            "time": self.event_time,
            "going": set(),
            "maybe": set(),
            "not_going": set(),
            "notified": False,
            "creator": self.user,
            "image_url": self.image_url
        }
        embed = generate_event_embed(event_id)
        view = EventView(event_id)
        
        # โพสต์กิจกรรมในช่องที่เลือก
        await selected_channel.send(embed=embed, view=view)

        await interaction.response.edit_message(content="✅ กิจกรรมถูกสร้างแล้ว", embed=embed, view=view)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ เฉพาะผู้สร้างเท่านั้นที่สามารถยกเลิกได้", ephemeral=True)
            return
        await interaction.response.edit_message(content="🚫 ยกเลิกการสร้างกิจกรรมแล้ว", embed=None, view=None)

@bot.tree.command(name="event", description="สร้างอีเวนต์ใหม่")
@app_commands.describe(title="หัวข้อ", description="รายละเอียด", time="เวลา (เช่น 11-04-2025 18:30)", image_url="ลิงก์รูปภาพ (ไม่บังคับ)")
async def create_event(interaction: discord.Interaction, title: str, description: str, time: str, image_url: str = None):
    try:
        event_time = datetime.strptime(time, "%d-%m-%Y %H:%M")
        event_time = THAI_TZ.localize(event_time).astimezone(pytz.utc)  # แปลงเป็น UTC
    except ValueError:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง! ใช้รูปแบบ: DD-MM-YYYY HH:MM", ephemeral=True)
        return

    embed = discord.Embed(title="🔍 ตรวจสอบกิจกรรมก่อนสร้าง", description=description, color=discord.Color.teal())
    embed.add_field(name="📌 หัวข้อ", value=title, inline=False)
    embed.add_field(name="🕒 เวลา", value=f"{event_time.astimezone(THAI_TZ).strftime('%d-%m-%Y %H:%M')} น.", inline=False)
    if image_url:
        embed.set_image(url=image_url)
    view = ConfirmEventView(title, description, event_time, image_url, interaction.user)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ==== ระบบหลักอื่น ๆ ====

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Logged in as {bot.user}')
    activity = discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.tree.command(name="ping", description="ทดสอบสถานะของบอท")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("บอทยังทำงานอยู่ 🟢")

@bot.tree.command(name="help", description="แสดงคำสั่งทั้งหมดของบอท")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📜 รายการคำสั่งของบอท", description="คำสั่งทั้งหมดที่สามารถใช้งานได้", color=discord.Color.blue())
    embed.add_field(name="/ping", value="ทดสอบว่าบอทออนไลน์หรือไม่", inline=False)
    embed.add_field(name="/event", value="สร้างอีเวนต์พร้อมปุ่มตอบรับ", inline=False)
    embed.add_field(name="/dm", value="ส่ง DM ให้กับสมาชิกที่อยู่ใน Role (เฉพาะแอดมิน)", inline=False)
    embed.add_field(name="ถาม [ข้อความ]", value="ถามคำถามทั่วไปกับ AI", inline=False)
    embed.set_footer(text="69Ranger Gentleman Community Bot")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# DM Broadcast (unchanged)... [ย่อเพื่อความชัดเจน]
# ...

# ✅ ป้องกันบอทหลับ
keep_alive()

# ✅ เริ่มรันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
