import discord
from discord.ext import commands
from discord import app_commands
import os
import openai
from keep_alive import keep_alive

# ตั้งค่า intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # ต้องเปิดใช้งานเพื่อให้บอทสามารถจับเหตุการณ์เมื่อมีสมาชิกใหม่เข้าร่วมเซิร์ฟเวอร์

# ตั้งค่า OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")  # ตั้งค่า API Key ของ OpenAI

# สร้างบอท
bot = commands.Bot(command_prefix='!', intents=intents)

# เมื่อบอทพร้อมใช้งาน
@bot.event
async def on_ready():
    await bot.tree.sync()  # ✅ Sync Slash Commands
    print(f'✅ Logged in as {bot.user}')
    activity = discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    await bot.change_presence(status=discord.Status.online, activity=activity)

# !ping (ปกติ)
@bot.command()
async def ping(ctx):
    await ctx.send('กำลังทำงาน [ปกติ]')

# ✅ /ping (Slash Command)
@bot.tree.command(name="ping", description="ทดสอบสถานะของบอท")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("บอทยังทำงานอยู่ 🟢")

# รองรับข้อความ "ถาม ..."
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("ถาม "):
        question = message.content[4:].strip()
        await message.channel.send("🤖 กำลังคิด...")
        try:
            # ส่งคำถามไปยัง OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "คุณคือผู้ช่วย AI ภาษาไทยที่สุภาพและให้ข้อมูลอย่างชัดเจน"},
                    {"role": "user", "content": question}
                ]
            )
            # รับคำตอบจาก OpenAI
            reply = response.choices[0].message['content']
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send(f"❌ เกิดข้อผิดพลาด: {e}")

    # ให้บอทจัดการคำสั่งที่ไม่ได้อยู่ใน on_message
    await bot.process_commands(message)

# เมื่อมีผู้เข้าร่วมเซิร์ฟเวอร์
@bot.event
async def on_member_join(member):
    try:
        # ข้อความต้อนรับ
        welcome_message = """สวัสดี! ยินดีต้อนรับสู่เซิร์ฟเวอร์ของเรา!
เราหวังว่าคุณจะมีความสนุกสนานและมีส่วนร่วมกับทุกคนที่นี่ :)
ถ้าคุณมีคำถามหรือปัญหา อย่าลังเลที่จะถาม!"""
        
        # ส่งข้อความต้อนรับไปยัง DM ของผู้ใช้
        await member.send(welcome_message)
        print(f"ส่งข้อความต้อนรับไปยัง {member.name}'s DM")
    except discord.Forbidden:
        # ถ้าไม่สามารถส่ง DM ได้ (ถ้าผู้ใช้ปิดการรับ DM)
        print(f"ไม่สามารถส่งข้อความต้อนรับให้ {member.name} ได้")

# ป้องกันบอทหลับ
keep_alive()

# รันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
