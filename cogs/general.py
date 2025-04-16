import discord
from discord.ext import commands
from datetime import datetime
import pytz

THAI_TZ = pytz.timezone("Asia/Bangkok")

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commands", description="แสดงคำสั่งทั้งหมดของบอท")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="📜 รายการคำสั่งของบอท",
            description="คำสั่งทั้งหมดที่สามารถใช้งานได้ในเซิร์ฟเวอร์นี้",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="⚙️ คำสั่งทั่วไป",
            value="`/ping` - ทดสอบว่าบอทออนไลน์หรือไม่\n"
                  "`/status` - แสดงสถานะของบอท\n"
                  "`/commands` - แสดงคำสั่งทั้งหมดของบอท",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(name="ping", description="ทดสอบสถานะของบอท")
    async def ping(self, ctx):
        await ctx.send("บอทยังทำงานอยู่ 🟢")

    @commands.command(name="status", description="แสดงสถานะของบอท")
    async def status(self, ctx):
        now = datetime.now(THAI_TZ)
        embed = discord.Embed(
            title="📊 สถานะของบอท",
            description="สถานะปัจจุบันของบอท",
            color=discord.Color.green()
        )
        embed.add_field(name="🟢 สถานะ", value="ออนไลน์", inline=False)
        embed.add_field(name="📅 เวลาปัจจุบัน", value=now.strftime("%d-%m-%Y %H:%M:%S"), inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))