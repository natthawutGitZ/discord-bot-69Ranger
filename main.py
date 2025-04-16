import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
import asyncio
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

# โหลดตัวแปรจาก .env
load_dotenv()

# Initialize bot and intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="Arma 3 | 69RangerGTMCommunit")
    )
    try:
        synced = await bot.tree.sync()
        print(f"✅ ซิงค์คำสั่ง {len(synced)} คำสั่งเรียบร้อยแล้ว")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการซิงค์คำสั่ง: {e}")

async def main():
    async with bot:
        # โหลด Cogs
        for cog in ["general", "admin", "events", "auto_role"]:
            try:
                await bot.load_extension(f"cogs.{cog}")
                print(f"✅ โหลด Cog {cog} สำเร็จ")
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการโหลด Cog {cog}: {e}")
        keep_alive()
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())