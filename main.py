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
#=============================================================================================
#⚠️ /event สร้าง event
class EventJoinView(discord.ui.View):
    def __init__(self, title, event_time):
        super().__init__(timeout=None)
        self.title = title
        self.event_time = event_time

    @discord.ui.button(label="✅ เข้าร่วม", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "going", button)

    @discord.ui.button(label="❔ อาจจะมา", style=discord.ButtonStyle.gray)
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "maybe", button)

    @discord.ui.button(label="❌ ไม่มา", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "declined", button)

   async def handle_response(self, interaction: discord.Interaction, status: str, button: discord.ui.Button):
        message_id = interaction.message.id
        user_id = interaction.user.id

        if message_id not in event_data:
            await interaction.response.send_message("❌ ไม่พบข้อมูลกิจกรรม", ephemeral=True)
            return

        for s in ["going", "maybe", "declined"]:
            if user_id in event_data[message_id][s]:
                event_data[message_id][s].remove(user_id)

        event_data[message_id][status].append(user_id)

        # แก้ไข embed
        embed = interaction.message.embeds[0]
        embed.set_field_at(4, name="📋 การเข้าร่วม", value=f"👍 เข้าร่วม: {len(event_data[message_id]['going'])}\n❔ อาจจะมา: {len(event_data[message_id]['maybe'])}\n❌ ไม่มา: {len(event_data[message_id]['declined'])}", inline=False)
        await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message(f"📌 คุณตอบว่า: {button.label}", ephemeral=True)

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
#⚠️ /Help แสดงคำสั่งทั้งหมดของบอท
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
#=============================================================================================
#⚠️ /ping ทดสอบสถานะของบอท
@bot.tree.command(name="ping", description="ทดสอบสถานะของบอท")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("บอทยังทำงานอยู่ 🟢")
#=============================================================================================
#⚠️ /DM ส่ง ข้อความ DM 
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
#=============================================================================================
#⚠️ auto Role  
@bot.event
async def on_member_join(member):
    try:
        role = discord.utils.get(member.guild.roles, name="Civilian")
        if role:
            await member.add_roles(role)
            print(f"✅ ให้ Role '{role.name}' กับ {member.name} แล้ว")
        else:
            print("❌ ไม่พบ Role 'Civilian'")
#=============================================================================================
#⚠️ welcome_message DM
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

#=============================================================================================
#⚠️ status Arma 3 | 69RangerGTMCommunit
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
#=============================================================================================
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
