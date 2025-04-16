import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dm", description="ส่ง DM ให้สมาชิกเฉพาะ Role (เฉพาะแอดมิน)")
    async def dm(self, ctx, role: discord.Role, *, message: str):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้ (ต้องเป็นแอดมิน)")
            return

        members = [m for m in role.members if not m.bot]
        if not members:
            await ctx.send("❌ ไม่มีสมาชิกใน Role นี้ที่สามารถส่ง DM ได้")
            return

        for member in members:
            try:
                await member.send(message)
            except discord.Forbidden:
                await ctx.send(f"❌ ไม่สามารถส่งข้อความให้ {member.name} ได้ (สมาชิกอาจปิดการรับ DM)")

        await ctx.send(f"✅ ส่งข้อความไปยังสมาชิกใน Role `{role.name}` เรียบร้อยแล้ว")

async def setup(bot):
    await bot.add_cog(Admin(bot))