import discord
from discord.ext import commands
from discord import app_commands
import os
from openai import OpenAI
from keep_alive import keep_alive

# ตั้งค่า intents
intents = discord.Intents.default()
intents.message_content = True

# OpenAI Client
openai_client = OpenAI()

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
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "คุณคือผู้ช่วย AI ภาษาไทยที่สุภาพและให้ข้อมูลอย่างชัดเจน"},
                    {"role": "user", "content": question}
                ]
            )
            reply = response.choices[0].message.content
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send(f"❌ เกิดข้อผิดพลาด: {e}")

    await bot.process_commands(message)

# ป้องกันบอทหลับ
keep_alive()

# รันบอท
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
