import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

# ตั้งค่า intents (ต้องเปิด intents ใน Discord Developer Portal ด้วย)
intents = discord.Intents.default()
intents.message_content = True  # ต้องเปิดอันนี้ถึงจะอ่านข้อความในแชทได้

# สร้างบอท
bot = commands.Bot(command_prefix='!', intents=intents)


# เมื่อบอทพร้อมใช้งาน
@bot.event
async def on_ready():
  print(f'✅ Logged in as {bot.user}')


# คำสั่งตัวอย่าง: !ping
@bot.command()
async def ping(ctx):
  await ctx.send('🏓 Pong!')


# สั่งให้รันเว็บป้องกันบอทหลับ (Replit)
keep_alive()

# รันบอท
TOKEN = os.getenv("DISCORD_TOKEN")  # ใส่ Token ผ่าน Environment Variable
bot.run(TOKEN)
