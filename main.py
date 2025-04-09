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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("ถาม "):
        question = message.content[4:]
        await message.channel.send("🤖 กำลังคิด...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "คุณคือผู้ช่วย AI ภาษาไทยที่สุภาพและให้ข้อมูลอย่างชัดเจน"},
                    {"role": "user", "content": question}
                ]
            )
            reply = response['choices'][0]['message']['content']
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send(f"❌ เกิดข้อผิดพลาด: {e}")

    await bot.process_commands(message)  # สำคัญมาก ถ้ายังใช้ @bot.command ร่วมด้วย
# รันเว็บกันบอทหลับ (Replit)
keep_alive()

# รันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
