import discord
from discord.ext import commands
from discord import app_commands
import os
import openai
from keep_alive import keep_alive
import asyncio
from datetime import datetime, timedelta

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
                    value=f"{data['time'].strftime('%A %d %B %Y %H:%M')} [Add to Google](https://calendar.google.com/calendar/render?action=TEMPLATE&text={data['title'].replace(' ', '+')}&dates={data['time'].strftime('%Y%m%dT%H%M00')}/{(data['time'] + timedelta(hours=2)).strftime('%Y%m%dT%H%M00')})",
                    inline=False)
    if "image_url" in data:
        embed.set_image(url=data["image_url"])
    embed.set_footer(text=f"Created by {data['creator'].display_name}")
    return embed

@bot.tree.command(name="event", description="สร้างอีเวนต์ใหม่")
@app_commands.describe(title="หัวข้อ", description="รายละเอียด", time="เวลา (เช่น 2025-04-11 18:30)", image_url="ลิงก์รูปภาพ (ไม่บังคับ)")
async def create_event(interaction: discord.Interaction, title: str, description: str, time: str, image_url: str = None):
    try:
        event_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message("❌ รูปแบบเวลาไม่ถูกต้อง! ใช้รูปแบบ: YYYY-MM-DD HH:MM", ephemeral=True)
        return

    event_id = len(event_data)
    event_data[event_id] = {
        "title": title,
        "description": description,
        "time": event_time,
        "going": set(),
        "maybe": set(),
        "not_going": set(),
        "notified": False,
        "creator": interaction.user,
        "image_url": image_url
    }

    embed = generate_event_embed(event_id)
    view = EventView(event_id)
    await interaction.response.send_message(embed=embed, view=view)

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

# DM Broadcast
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
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith("ถาม "):
        question = message.content[4:].strip()
        await message.channel.send("🤖 กำลังคิด...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "คุณคือผู้ช่วย AI ภาษาไทยที่สุภาพและให้ข้อมูลอย่างชัดเจน"},
                    {"role": "user", "content": question}
                ]
            )
            reply = response.choices[0].message['content']
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send(f"❌ เกิดข้อผิดพลาด: {e}")
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    try:
        role_name = "Civilian"
        guild = member.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
            print(f"✅ ให้ Role '{role.name}' กับ {member.name} แล้ว")
        else:
            print(f"❌ ไม่พบ Role ชื่อ '{role_name}'")
        welcome_message = ("สวัสดี! ยินดีต้อนรับสู่เซิร์ฟเวอร์ของเรา!\n"
                           "เราหวังว่าคุณจะมีความสนุกสนานและมีส่วนร่วมกับทุกคนที่นี่ :)\n"
                           "ถ้าคุณมีคำถามหรือปัญหา สอบถามได้ที่ <#1281566308097462335>\n"
                           "หากต้องการเข้าร่วม สามารถกรอกใบสมัครได้ที่ <#1349726875030913085>")
        await member.send(welcome_message)
        print(f"✅ ส่งข้อความต้อนรับไปยัง {member.name}'s DM")
    except discord.Forbidden:
        print(f"❌ ไม่สามารถส่งข้อความให้ {member.name} ได้")

# ✅ ป้องกันบอทหลับ
keep_alive()

# ✅ เริ่มรันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
