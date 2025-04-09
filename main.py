import discord
from discord.ext import commands
import os
import openai  # เพิ่มมาใหม่
from keep_alive import keep_alive

# ตั้งค่า intents (ต้องเปิด intents ใน Discord Developer Portal ด้วย)
intents = discord.Intents.default()
intents.message_content = True

# สร้างบอท
bot = commands.Bot(command_prefix='!', intents=intents)

# ตั้งค่า OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")  # ใส่ key ผ่าน environment

# เมื่อบอทพร้อมใช้งาน
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    activity = discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    await bot.change_presence(status=discord.Status.online, activity=activity)

# คำสั่งตัวอย่าง: !ping
@bot.command()
async def ping(ctx):
    await ctx.send(' กำลังทำงาน [ปกติ ]')

# คำสั่ง AI: !ถาม <คำถาม>
@bot.command()
async def AI(ctx, *, message):
    await ctx.send("🤖 กำลังคิด...")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # หรือ gpt-4 ถ้าคุณมีสิทธิ์
            messages=[
                {"role": "system", "content": "คุณคือผู้ช่วย AI ภาษาไทยที่สุภาพและให้ข้อมูลอย่างชัดเจน"},
                {"role": "user", "content": message}
            ]
        )
        reply = response['choices'][0]['message']['content']
        await ctx.send(reply)
    except Exception as e:
        await ctx.send(f"❌ เกิดข้อผิดพลาด: {e}")

# รันเว็บกันบอทหลับ (Replit)
keep_alive()

# รันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
