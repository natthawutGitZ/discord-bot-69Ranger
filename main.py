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
    def __init__(self, interaction):
        options = [
            discord.SelectOption(label=channel.name, value=str(channel.id))
            for channel in interaction.guild.text_channels
        ]
        super().__init__(placeholder="เลือกช่องสำหรับอีเวนต์", min_values=1, max_values=1, options=options)


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

    # วันในสัปดาห์ ภาษาไทย
    weekday_thai = {
        0: "วันจันทร์",
        1: "วันอังคาร",
        2: "วันพุธ",
        3: "วันพฤหัสบดี",
        4: "วันศุกร์",
        5: "วันเสาร์",
        6: "วันอาทิตย์"
    }

    # เดือน ภาษาไทย
    thai_months = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]

    # แปลงวันเวลา
    weekday = weekday_thai[local_time.weekday()]
    day = local_time.day
    month = thai_months[local_time.month]
    year = local_time.year + 543  # พ.ศ.
    time_str = local_time.strftime("%H:%M")

    # สร้างข้อความเวลาแบบไทย
    thai_time_str = f"{weekday}ที่ {day} {month} {year} เวลา {time_str} น."
    embed = discord.Embed(
        title=f"📌 Operation: {data['title']}",
        description=data["description"],
        color=discord.Color.dark_red()
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
    def __init__(self, title, description, event_time, image_url, interaction):
        super().__init__(timeout=None)
        self.title = title
        self.description = description
        self.event_time = event_time
        self.image_url = image_url
        self.user = interaction
        self.channel_select = ChannelSelect(interaction)
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
    view = ConfirmEventView(title, description, event_time, image_url, interaction)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ==== ระบบหลักอื่น ๆ ====

# ✅ แสดงสถานะ Arma 3 | 69RangerGTMCommunit | ✅ แสดงคำสั่ง Slash บนหน้า Bot Profile
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Logged in as {bot.user}')
    
    # เปลี่ยนสถานะเป็น Arma 3 | 69RangerGTMCommunit
    activity = discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    try:
        synced = await bot.tree.sync()  # Global Sync
        print(f"✅ Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    for cmd in bot.tree.get_commands():
        print(f"📌 Synced command: /{cmd.name}")

# ✅ ปุ่มยืนยันก่อนส่งข้อความ
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


# ✅ Help แสดงคำสั่งทั้งหมดของบอท
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


# ✅ Ping (Slash)
@bot.tree.command(name="ping", description="ทดสอบสถานะของบอท")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("บอทยังทำงานอยู่ 🟢")

# ✅ Slash Command: /dm
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

# ✅ ถาม AI ด้วย OpenAI API
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

# ✅ Auto Role ให้กับสมาชิกใหม่
# ✅ ต้อนรับสมาชิกใหม่
@bot.event
async def on_member_join(member):
    try:
        # ให้ Role
        role_name = "Civilian"
        role = discord.utils.get(member.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
            print(f"✅ ให้ Role '{role.name}' กับ {member.name} แล้ว")
        else:
            print(f"❌ ไม่พบ Role '{role_name}'")

        # ส่งข้อความต้อนรับ
        welcome_message = """สวัสดี! ยินดีต้อนรับสู่เซิร์ฟเวอร์ของเรา!
เราหวังว่าคุณจะมีความสนุกสนานและมีส่วนร่วมกับทุกคนที่นี่ :)
ถ้าคุณมีคำถามหรือปัญหา สอบถามได้ที่ <#1281566308097462335>
หากต้องการเข้าร่วม สามารถกรอกใบสมัครได้ที่ <#1349726875030913085>"""
        await member.send(welcome_message)
        print(f"✅ ส่งข้อความต้อนรับไปยัง {member.name}'s DM")
    except discord.Forbidden:
        print(f"❌ ไม่สามารถส่งข้อความให้ {member.name} ได้")




# ✅ ป้องกันบอทหลับ
keep_alive()

# ✅ เริ่มรันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
