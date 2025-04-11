import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import pytz
import os
from keep_alive import keep_alive
import asyncio

# ตั้งค่า intents
intents = discord.Intents.default()
intents.message_content = True
INTENTS = discord.Intents.all()
intents.members = True

# เก็บข้อมูล event ชั่วคราวในหน่วยความจำ
event_data = {}  

# สร้างบอท
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.command()
async def สร้างอีเว้น(ctx, *, รายละเอียด=None):
    title = "Operation: NAME "
    description = "Description Story"
    time_str = "30 มีนาคม 2568 21:00"
    
    # ใช้เวลาจริง (แก้ตรงนี้ให้รองรับ input ได้ในอนาคต)
    event_time = datetime.datetime(2025, 3, 30, 21, 0, tzinfo=pytz.timezone("Asia/Bangkok"))

    embed = discord.Embed(title=title, description=description, color=0x3399ff)
    embed.add_field(name="🕒 เวลา", value=f"{time_str} (เวลาไทย)", inline=False)
    embed.add_field(name="✅ เข้าร่วม", value="ยังไม่มี", inline=True)
    embed.add_field(name="❌ ไม่เข้าร่วม", value="ยังไม่มี", inline=True)
    embed.add_field(name="❔ อาจจะเข้าร่วม", value="ยังไม่มี", inline=True)
    embed.set_footer(text=f"Created by {ctx.author.display_name}")

    # สร้างปุ่ม
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="✅", custom_id="accept", style=discord.ButtonStyle.success))
    view.add_item(discord.ui.Button(label="❌", custom_id="decline", style=discord.ButtonStyle.danger))
    view.add_item(discord.ui.Button(label="❔", custom_id="tentative", style=discord.ButtonStyle.primary))
    view.add_item(discord.ui.Button(label="📝 Edit", custom_id="edit", style=discord.ButtonStyle.secondary))
    view.add_item(discord.ui.Button(label="🗑 Delete", custom_id="delete", style=discord.ButtonStyle.danger))

    msg = await ctx.send(embed=embed, view=view)

    # สร้าง Thread สำหรับ event นี้
    thread = await msg.create_thread(name=title)

    # เก็บข้อมูล
    event_data[msg.id] = {
        "owner": ctx.author.id,
        "time": event_time,
        "thread_id": thread.id,
        "responses": {
            "accept": [],
            "decline": [],
            "tentative": []
        }
    }



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
        
    async def on_interaction(interaction: discord.Interaction):
    if not interaction.type == discord.InteractionType.component:
        return

    msg_id = interaction.message.id
    user = interaction.user
    cid = interaction.data["custom_id"]

    if msg_id not in event_data:
        return

    data = event_data[msg_id]

    if cid == "delete":
        if user.id == data["owner"]:
            await interaction.message.delete()
            del event_data[msg_id]
        else:
            await interaction.response.send_message("คุณไม่สามารถลบ event นี้ได้", ephemeral=True)
        return

    if cid in ["accept", "decline", "tentative"]:
        # เคลียร์ชื่อจากทุกกลุ่มก่อน
        for key in data["responses"]:
            if user.display_name in data["responses"][key]:
                data["responses"][key].remove(user.display_name)
        data["responses"][cid].append(user.display_name)

        # อัปเดต Embed
        embed = interaction.message.embeds[0]
        embed.set_field_at(1, name="✅ เข้าร่วม", value="\n".join(data["responses"]["accept"]) or "ยังไม่มี", inline=True)
        embed.set_field_at(2, name="❌ ไม่เข้าร่วม", value="\n".join(data["responses"]["decline"]) or "ยังไม่มี", inline=True)
        embed.set_field_at(3, name="❔ อาจจะเข้าร่วม", value="\n".join(data["responses"]["tentative"]) or "ยังไม่มี", inline=True)

        await interaction.response.edit_message(embed=embed)

@tasks.loop(minutes=1)
async def check_event():
    now = datetime.datetime.now(pytz.timezone("Asia/Bangkok"))
    for msg_id in list(event_data.keys()):
        data = event_data[msg_id]
        seconds_left = (data["time"] - now).total_seconds()

        if 0 <= seconds_left <= 600:
            thread = bot.get_channel(data["thread_id"])
            if thread:
                await thread.send(
                    f"🔔 เตือนความจำ: อีก 10 นาทีจะเริ่มกิจกรรม!\n"
                    f"ผู้เข้าร่วม ({len(data['responses']['accept'])} คน):\n"
                    + "\n".join(data["responses"]["accept"])
                )
            del event_data[msg_id]




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

# ✅ Auto Role ให้กับสมาชิกใหม่
@bot.event
async def on_member_join(member):
    try:
        # 👇 ใส่ชื่อ Role ที่ต้องการให้สมาชิกใหม่ได้รับ
        role_name = "Civilian"
        guild = member.guild
        role = discord.utils.get(guild.roles, name=role_name)
        
        if role:
            await member.add_roles(role)
            print(f"✅ ให้ Role '{role.name}' กับ {member.name} แล้ว")
        else:
            print(f"❌ ไม่พบ Role ชื่อ '{role_name}'")

# ✅ ต้อนรับสมาชิกใหม่
@bot.event
async def on_member_join(member):
    try:
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




