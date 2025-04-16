import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive
import asyncio
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.DEBUG)


# Initialize bot and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

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
            "`/dm` - ส่งข้อความ DM ให้สมาชิกใน Role"
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
#⚠️ auto Role  เพิ่ม Role ให้สมาชิกใหม่
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
# ⚠️ ส่งข้อความต้อนรับผ่าน DM
    try:
        welcome_message = (
            "สวัสดี! ยินดีต้อนรับสู่เซิร์ฟเวอร์ของเรา!\n"
            "เราหวังว่าคุณจะมีความสนุกสนานและมีส่วนร่วมกับทุกคนที่นี่ :)\n"
            "ถ้าคุณมีคำถามหรือปัญหา สอบถามได้ที่ <#1281566308097462335>\n"
            "หากต้องการเข้าร่วม สามารถกรอกใบสมัครได้ที่ <#1349726875030913085>"
        )
        await member.send(welcome_message)
        print(f"✅ ส่งข้อความต้อนรับไปยัง {member.name}'s DM")
    except discord.Forbidden:
        print(f"❌ ไม่สามารถส่งข้อความให้ {member.name} ได้ (สมาชิกอาจปิดการรับ DM)")
        channel = discord.utils.get(member.guild.text_channels, name="🧰𝐜𝐨𝐦𝐦𝐚𝐧𝐝𝐬-𝐛𝐨𝐭-𝐥𝐨𝐠")  # เปลี่ยนชื่อช่องตามต้องการ
        if channel:
            await channel.send(f"ยินดีต้อนรับ {member.mention}! โปรดเปิดการรับข้อความ DM เพื่อรับข้อมูลเพิ่มเติม.")

#=============================================================================================
#⚠️ status Arma 3 | 69RangerGTMCommunit
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    )
    try:
        synced = await bot.tree.sync()  # ซิงค์คำสั่งกับ Discord
        print(f"✅ ซิงค์คำสั่ง {len(synced)} คำสั่งเรียบร้อยแล้ว")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการซิงค์คำสั่ง: {e}")

#=============================================================================================
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))