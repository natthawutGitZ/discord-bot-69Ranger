import discord
from discord.ext import commands
from discord import app_commands
import os
import openai
from keep_alive import keep_alive
import asyncio

# ตั้งค่า intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# สร้างบอท
bot = commands.Bot(command_prefix='!', intents=intents)

# ตั้งค่า OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ แสดงสถานะ Arma 3 | 69RangerGTMCommunit
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Logged in as {bot.user}')
    activity = discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    await bot.change_presence(status=discord.Status.online, activity=activity)

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

# ✅ เมื่อบอทพร้อม
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Logged in as {bot.user}')
    activity = discord.Game(name="Arma 3 | 69RangerGTMCommunity")
    await bot.change_presence(status=discord.Status.online, activity=activity)

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

# ✅ แสดงคำสั่ง Slash บนหน้า Bot Profile
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()  # <-- Global Sync
        print(f"✅ Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"❌ Sync failed: {e}")


# ✅ ป้องกันบอทหลับ
keep_alive()

# ✅ เริ่มรันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
