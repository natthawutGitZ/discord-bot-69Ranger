import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive
import asyncio
from datetime import datetime, timedelta


# Initialize bot and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

event_data = {}

from babel.dates import format_datetime
from datetime import datetime
import pytz

THAI_TZ = pytz.timezone("Asia/Bangkok")
now = datetime.now(THAI_TZ)

formatted_date = format_datetime(now, "EEEE d MMMM yyyy HH:mm", locale="th")
print(formatted_date)

import locale
try:
    locale.setlocale(locale.LC_TIME, "th_TH.UTF-8")  # ตั้งค่าภาษาไทยสำหรับวันที่
except locale.Error:
    print("❌ Locale 'th_TH.UTF-8' is not supported. Falling back to default locale.")
    locale.setlocale(locale.LC_TIME, "")  # ใช้ locale เริ่มต้นของระบบแทน

def format_event_time(start_time: datetime, end_time: datetime, timezone: pytz.timezone) -> str:
    """จัดรูปแบบวันเวลาในภาษาไทย พร้อมแสดงเวลาที่เหลือหรือเวลาที่ผ่านมา"""
    start_local = start_time.astimezone(timezone)
    end_local = end_time.astimezone(timezone)

    # แปลงวันที่เป็นภาษาไทย
    start_date = format_datetime(start_local, "EEEE d MMMM yyyy HH:mm", locale="th")
    end_time_str = end_local.strftime("%H:%M")

    # คำนวณเวลาปัจจุบัน
    now = datetime.now(timezone)
    if now < start_local:
        # เหลือเวลาอีก
        time_diff = start_local - now
        if time_diff.days > 0:
            time_text = f"เหลือเวลาอีก {time_diff.days} วัน"
        else:
            hours = time_diff.seconds // 3600
            minutes = (time_diff.seconds % 3600) // 60
            if hours > 0:
                time_text = f"เหลือเวลาอีก {hours} ชั่วโมง"
            else:
                time_text = f"เหลือเวลาอีก {minutes} นาที"
    elif now > end_local:
        # ผ่านมาแล้ว
        time_diff = now - end_local
        if time_diff.days > 0:
            time_text = f"{time_diff.days} วันที่ผ่านมา"
        else:
            hours = time_diff.seconds // 3600
            minutes = (time_diff.seconds % 3600) // 60
            if hours > 0:
                time_text = f"{hours} ชั่วโมงที่ผ่านมา"
            else:
                time_text = f"{minutes} นาทีที่ผ่านมา"
    else:
        # กำลังเกิดขึ้น
        time_text = "กำลังดำเนินการ"

    # สร้างข้อความ
    return f"{start_date} - {end_time_str} | {time_text}"
#=============================================================================================
# Load token from environment variable ฟังก์ชันนี้จะจัดรูปแบบรายชื่อผู้ใช้ในแต่ละสถานะให้อยู่ในรูปแบบแนวตั้ง (แสดงชื่อผู้ใช้แต่ละคนในแต่ละบรรทัด):
def format_names(user_ids, guild):
    """Format user names for display."""
    if not user_ids:
        return None
    names = []
    for uid in user_ids:
        member = guild.get_member(uid)
        if member:
            names.append(f"{member.display_name}")
    return "\n".join(names)
#=============================================================================================
# EventJoinView class for handling event responses
class EventJoinView(discord.ui.View):
    def __init__(self, title, event_time, creator_id):
        super().__init__(timeout=None)  # ตั้งค่า timeout=None เพื่อป้องกัน View หมดอายุ
        self.title = title
        self.event_time = event_time
        self.creator_id = creator_id
        print("📌 EventJoinView ถูกสร้างขึ้น")

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
    
        # Format user names for each status
        going_names = format_names(event_data[message_id]["going"], interaction.guild)
        maybe_names = format_names(event_data[message_id]["maybe"], interaction.guild)
        declined_names = format_names(event_data[message_id]["declined"], interaction.guild)
    
        # Ensure fields exist before updating
        fields = embed.fields
        while len(fields) < 6:  # Ensure there are at least 6 fields
            embed.add_field(name="Placeholder", value="-", inline=True)
    
        # Update the embed fields with column layout
        embed.set_field_at(
            4,
            name=f"✅ Accepted ({len(event_data[message_id]['going'])})",
            value=going_names or "- ไม่มี -",
            inline=True
        )
        embed.set_field_at(
            5,
            name=f"❔ Tentative ({len(event_data[message_id]['maybe'])})",
            value=maybe_names or "- ไม่มี -",
            inline=True
        )
        embed.set_field_at(
            6,
            name=f"❌ Declined ({len(event_data[message_id]['declined'])})",
            value=declined_names or "- ไม่มี -",
            inline=True
        )
    
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"📌 คุณตอบว่า: {button.label}", ephemeral=True)
    # Buttons for event responses
    @discord.ui.button(label="✅ เข้าร่วม", style=discord.ButtonStyle.success, row=0)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("📌 Callback ถูกเรียกใช้งาน")
        await self.handle_response(interaction, "going", button)

    @discord.ui.button(label="❔ อาจจะมา", style=discord.ButtonStyle.primary, row=0)
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "maybe", button)

    @discord.ui.button(label="❌ ไม่มา", style=discord.ButtonStyle.danger, row=0)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_response(interaction, "declined", button)


    # ฟังก์ชัน on_timeout สำหรับจัดการเมื่อ View หมดเวลา
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True  # ปิดการใช้งานปุ่มทั้งหมด
        try:
            await self.message.edit(content="⏳ เวลาหมดอายุสำหรับการตอบกลับ", view=self)
        except discord.NotFound:
            print("❌ ไม่สามารถแก้ไขข้อความได้ (ข้อความถูกลบไปแล้ว)")

    # Button for editing the event
    @discord.ui.button(label="✏️ แก้ไข", style=discord.ButtonStyle.blurple, row=1)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ คุณไม่มีสิทธิ์แก้ไขกิจกรรมนี้", ephemeral=True)
            return
        await interaction.response.send_message("📋 โปรดส่งข้อมูลใหม่สำหรับกิจกรรมนี้ (ยังไม่ได้เพิ่มฟังก์ชันแก้ไข)", ephemeral=True)

    @discord.ui.button(label="🗑️ ลบ", style=discord.ButtonStyle.red, row=1)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ลบกิจกรรมนี้", ephemeral=True)
            return

        # ลบข้อความและข้อมูลกิจกรรม
        message_id = interaction.message.id
        if message_id in event_data:
            del event_data[message_id]

        await interaction.message.delete()
        await interaction.response.send_message("🗑️ กิจกรรมถูกลบเรียบร้อยแล้ว", ephemeral=True)

#=============================================================================================
# Command to create a new event
@bot.tree.command(name="event", description="สร้างอีเวนต์ใหม่")
@app_commands.describe(
    title="หัวข้ออีเวนต์",
    editor_info="Editor by | PresetMod",
    story="เนื้อเรื่องของภารกิจ",
    roles="บทบาทที่รับ (75ranger)",
    start_time="เวลาเริ่มต้น (เช่น 30-03-2025 21:00)",
    end_time="เวลาสิ้นสุด (เช่น 30-03-2025 23:59)",
    channel="ห้องที่ต้องการโพสต์อีเวนต์",
    image_url="ลิงก์รูปภาพ URL (ไม่บังคับ)"
)
async def create_event(
    interaction: discord.Interaction,
    title: str,
    editor_info: str,
    story: str,
    roles: str,
    start_time: str,
    end_time: str,
    channel: discord.TextChannel,
    image_url: str = None
):
    try:
        # แปลงเวลาเริ่มต้นและเวลาสิ้นสุด
        start_time_dt = datetime.strptime(start_time, "%d-%m-%Y %H:%M")
        end_time_dt = datetime.strptime(end_time, "%d-%m-%Y %H:%M")
        start_time_utc = THAI_TZ.localize(start_time_dt).astimezone(pytz.utc)
        end_time_utc = THAI_TZ.localize(end_time_dt).astimezone(pytz.utc)

        # จัดรูปแบบวันเวลา
        formatted_time = format_event_time(start_time_utc, end_time_utc, THAI_TZ)

        # สร้าง Embed
        embed = discord.Embed(title=title.upper().replace("#", ""), color=discord.Color.green())  # ใช้ .upper() เพื่อแปลง title เป็นตัวใหญ่
        embed.add_field(name="🛠️ Editor | PresetMod", value=editor_info, inline=False)
        embed.add_field(name="📖 Story", value=story, inline=False)
        embed.add_field(name="⭐ Roles", value=roles, inline=False)
        embed.add_field(name="🕒 วันและเวลา", value=formatted_time, inline=False)
        embed.add_field(name="📋 การเข้าร่วม", value="✅ เข้าร่วม: 0\n❔ อาจจะมา: 0\n❌ ไม่มา: 0", inline=False)

        if image_url:
            embed.set_image(url=image_url)

        view = EventJoinView(title, start_time_utc, interaction.user.id)
        msg = await channel.send(embed=embed, view=view)

        thread = await msg.create_thread(name=f"🗓️ {title.upper()}", auto_archive_duration=60)  # ใช้ .upper() สำหรับชื่อ Thread
        await thread.send(f"📢 กิจกรรม `{title.upper()}` ถูกสร้างโดย <@{interaction.user.id}>")  # ใช้ .upper() สำหรับข้อความ

        event_data[msg.id] = {
            "title": title,
            "event_time": start_time_utc,
            "going": [],
            "maybe": [],
            "declined": [],
            "thread_id": thread.id,
            "message_id": msg.id,
            "channel_id": channel.id
        }

        await interaction.response.send_message("✅ กิจกรรมถูกสร้างเรียบร้อยแล้ว!", ephemeral=True)

    except ValueError:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง! ใช้รูปแบบ: DD-MM-YYYY HH:MM", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ เกิดข้อผิดพลาด: {e}", ephemeral=True)
#=============================================================================================
#⚠️ /Help แสดงคำสั่งทั้งหมดของบอท
@bot.tree.command(name="help", description="แสดงคำสั่งทั้งหมดของบอท")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 รายการคำสั่งของบอท",
        description="คำสั่งทั้งหมดที่สามารถใช้งานได้ในเซิร์ฟเวอร์นี้",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="⚙️ คำสั่งทั่วไป",
        value=(
            "`/ping` - ทดสอบว่าบอทออนไลน์หรือไม่\n"
            "`/status` - แสดงสถานะของบอท\n"
            "`/help` - แสดงคำสั่งทั้งหมดของบอท"
        ),
        inline=False
    )
    embed.add_field(
        name="📩 คำสั่งสำหรับแอดมิน",
        value=(
            "`/dm` - ส่งข้อความ DM ให้สมาชิกใน Role\n"
            "`/event` - สร้างอีเวนต์ใหม่"
        ),
        inline=False
    )
    embed.add_field(
        name="🎮 คำสั่งเกี่ยวกับกิจกรรม",
        value=(
            "`/event` - สร้างอีเวนต์ใหม่พร้อมปุ่มตอบรับ\n"
            "สามารถใช้เพื่อจัดการกิจกรรมในเซิร์ฟเวอร์"
        ),
        inline=False
    )
    embed.set_footer(
        text="69Ranger Gentleman Community Bot | พัฒนาโดย | Silver BlackWell", 
        icon_url="https://cdn-icons-png.flaticon.com/512/847/847969.png"  # เพิ่มไอคอนใน Footer
    )
    embed.set_thumbnail(
        url="https://cdn-icons-png.flaticon.com/512/847/847969.png"  # เพิ่มไอคอนใน Thumbnail
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
#=============================================================================================
#⚠️ /ping ทดสอบสถานะของบอท
@bot.tree.command(name="ping", description="ทดสอบสถานะของบอท")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("บอทยังทำงานอยู่ 🟢")
#=============================================================================================
#⚠️  /status เพื่อแสดงสถานะของบอท
@bot.tree.command(name="status", description="แสดงสถานะของบอท")
async def status_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 สถานะของบอท",
        description="สถานะปัจจุบันของบอท",
        color=discord.Color.green()
    )
    embed.add_field(name="🟢 สถานะ", value="ออนไลน์", inline=False)
    embed.add_field(name="📅 เวลาปัจจุบัน", value=datetime.now(THAI_TZ).strftime("%d-%m-%Y %H:%M:%S"), inline=False)
    embed.set_footer(text="69Ranger Gentleman Community Bot")
    await interaction.response.send_message(embed=embed, ephemeral=True)
#=============================================================================================
#⚠️ /DM ส่ง ข้อความ DM 
class ConfirmView(discord.ui.View):
    def __init__(self, role, message, members):
        super().__init__(timeout=None)  # ตั้งค่า timeout=None เพื่อป้องกัน View หมดอายุ
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
            if member.guild.me.guild_permissions.manage_roles:
                await member.add_roles(role)
                print(f"✅ ให้ Role '{role.name}' กับ {member.name} แล้ว")
            else:
                print("❌ บอทไม่มีสิทธิ์ในการจัดการ Role")
        else:
            print("❌ ไม่พบ Role 'Civilian'")
    except discord.Forbidden:
        print(f"❌ ไม่สามารถเพิ่ม Role ให้ {member.name} ได้ (ไม่มีสิทธิ์)")
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
    print(f'✅ Logged in as {bot.user}')
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    )
    
#=============================================================================================
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
