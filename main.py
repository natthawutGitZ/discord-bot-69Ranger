import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive
import asyncio
from datetime import datetime
import pytz

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
event_data = {}
THAI_TZ = pytz.timezone("Asia/Bangkok")

class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, event_data):
        super().__init__(
            placeholder='เลือกห้องที่ต้องการโพสต์กิจกรรม',
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]
        )
        self.event_data = event_data

class ConfirmEventView(discord.ui.View):
    def __init__(self, title, description, event_time, image_url, interaction):
        super().__init__(timeout=None)
        self.user = interaction.user
        self.title = title
        self.description = description
        self.event_time = event_time
        self.image_url = image_url
        event_data_temp = {
            "title": title,
            "description": description,
            "event_time": event_time,
            "image_url": image_url
        }
        self.channel_select = ChannelSelect(event_data_temp)
        self.add_item(self.channel_select)

    @discord.ui.button(label="ยืนยัน", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("คุณไม่สามารถยืนยันกิจกรรมนี้ได้", ephemeral=True)
            return

        selected_channel = interaction.guild.get_channel(int(self.channel_select.values[0]))
        embed = discord.Embed(title=self.title, description=self.description, color=discord.Color.green())
        embed.add_field(name="🕒 วันและเวลา", value=self.event_time.strftime("%d/%m/%Y %H:%M"))
        if self.image_url:
            embed.set_image(url=self.image_url)

        await selected_channel.send(embed=embed)
        await interaction.response.send_message("กิจกรรมถูกโพสต์เรียบร้อยแล้ว", ephemeral=True)
        self.stop()

    @discord.ui.button(label="ยกเลิก", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("คุณไม่สามารถยกเลิกกิจกรรมนี้ได้", ephemeral=True)
            return

        await interaction.response.send_message("การสร้างกิจกรรมถูกยกเลิก", ephemeral=True)
        self.stop()

@bot.tree.command(name="event", description="สร้างอีเวนต์ใหม่")
@app_commands.describe(title="หัวข้อ", description="รายละเอียด", time="เวลา (เช่น 11-04-2025 18:30)", image_url="ลิงก์รูปภาพ (ไม่บังคับ)")
async def create_event(interaction: discord.Interaction, title: str, description: str, time: str, image_url: str = None):
    try:
        event_time = datetime.strptime(time, "%d-%m-%Y %H:%M")
        event_time = THAI_TZ.localize(event_time).astimezone(pytz.utc)
    except ValueError:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง! ใช้รูปแบบ: DD-MM-YYYY HH:MM", ephemeral=True)
        return

    embed = discord.Embed(title="🔍 ตรวจสอบกิจกรรมก่อนสร้าง", description=description, color=discord.Color.teal())
    embed.add_field(name="📌 หัวข้อ", value=title, inline=False)
    embed.add_field(name="🕒 เวลา", value=f"{event_time.astimezone(THAI_TZ).strftime('%d-%m-%Y %H:%M')} น.", inline=False)
    if image_url:
        embed.set_image(url=image_url)

    view = ConfirmEventView(title, description, event_time, image_url, interaction)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="help", description="แสดงคำสั่งทั้งหมดของบอท")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 รายการคำสั่งของบอท",
        description="คำสั่งทั้งหมดที่สามารถใช้งานได้",
        color=discord.Color.blue()
    )
    embed.add_field(name="/ping", value="ทดสอบว่าบอทออนไลน์หรือไม่", inline=False)
    embed.add_field(name="/dm", value="ส่ง DM ให้กับสมาชิกที่อยู่ใน Role (เฉพาะแอดมิน)", inline=False)
    embed.add_field(name="ถาม [ข้อความ]", value="ถามคำถามทั่วไปกับ AI", inline=False)
    embed.set_footer(text="69Ranger Gentleman Community Bot")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="ทดสอบสถานะของบอท")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("บอทยังทำงานอยู่ 🟢")

class ConfirmView(discord.ui.View):
    def __init__(self, role, message, members):
        super().__init__(timeout=60)
        self.role = role
        self.message = message
        self.members = members

    @discord.ui.button(label="✅ ยืนยัน", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="📤 เริ่มส่งข้อความ...", view=None)
        success = 0
        failed = 0
        for member in self.members:
            try:
                await member.send(self.message)
                success += 1
            except:
                failed += 1
            await asyncio.sleep(1)

        await interaction.followup.send(f"✅ ส่งสำเร็จ: {success} คน\n❌ ส่งไม่สำเร็จ: {failed} คน", ephemeral=True)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🚫 ยกเลิกการส่งข้อความ", view=None)

@bot.tree.command(name="dm", description="ส่ง DM ให้สมาชิกเฉพาะ Role (เฉพาะแอดมิน)")
@app_commands.describe(role="เลือก Role ที่ต้องการส่งถึง", message="ข้อความที่จะส่ง")
async def dm(interaction: discord.Interaction, role: discord.Role, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้ (ต้องเป็นแอดมิน)", ephemeral=True)
        return

    members = [m for m in role.members if not m.bot]
    if not members:
        await interaction.response.send_message("❌ ไม่มีสมาชิกใน Role นี้ที่สามารถส่ง DM ได้", ephemeral=True)
        return

    view = ConfirmView(role, message, members)
    await interaction.response.send_message(
        f"⚠️ คุณต้องการส่งข้อความนี้ให้กับ `{len(members)}` คนใน Role `{role.name}` หรือไม่?\n\n📨 ข้อความ:\n```{message}```",
        view=view,
        ephemeral=True
    )

@bot.event
async def on_member_join(member):
    try:
        role = discord.utils.get(member.guild.roles, name="Civilian")
        if role:
            await member.add_roles(role)
            print(f"✅ ให้ Role '{role.name}' กับ {member.name} แล้ว")
        else:
            print("❌ ไม่พบ Role 'Civilian'")

        welcome_message = (
            "สวัสดี! ยินดีต้อนรับสู่เซิร์ฟเวอร์ของเรา!\n"
            "เราหวังว่าคุณจะมีความสนุกสนานและมีส่วนร่วมกับทุกคนที่นี่ :)\n"
            "ถ้าคุณมีคำถามหรือปัญหา สอบถามได้ที่ <#1281566308097462335>\n"
            "หากต้องการเข้าร่วม สามารถกรอกใบสมัครได้ที่ <#1349726875030913085>"
        )
        await member.send(welcome_message)
        print(f"✅ ส่งข้อความต้อนรับไปยัง {member.name}'s DM")
    except discord.Forbidden:
        print(f"❌ ไม่สามารถส่งข้อความให้ {member.name} ได้")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Logged in as {bot.user}')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Arma 3 | 69RangerGTMCommunit"))
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    for cmd in bot.tree.get_commands():
        print(f"📌 Synced command: /{cmd.name}")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
