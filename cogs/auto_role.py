import discord
from discord.ext import commands

class AutoRole(commands.Cog):
    """
    Cog สำหรับจัดการ Auto Role และข้อความต้อนรับ
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Event: เพิ่ม Role ให้สมาชิกใหม่และส่งข้อความต้อนรับ
        """
        # กำหนดชื่อ Role ที่ต้องการเพิ่ม
        role_name = "Civilian"  # เปลี่ยนชื่อ Role ตามที่ต้องการ
        role = discord.utils.get(member.guild.roles, name=role_name)

        if role:
            try:
                # เพิ่ม Role ให้สมาชิกใหม่
                await member.add_roles(role)
                print(f"✅ เพิ่ม Role '{role_name}' ให้กับ {member.name} สำเร็จ")
            except discord.Forbidden:
                print(f"❌ ไม่สามารถเพิ่ม Role '{role_name}' ให้กับ {member.name} (ไม่มีสิทธิ์)")
        else:
            print(f"❌ ไม่พบ Role '{role_name}' ในเซิร์ฟเวอร์")

        # ส่งข้อความต้อนรับผ่าน DM
        try:
            welcome_message = (
                f"สวัสดี {member.mention}! ยินดีต้อนรับสู่เซิร์ฟเวอร์ของเรา 🎉\n"
                "โปรดอ่านกฎในช่อง <#1211204645410570261> และสนุกกับการพูดคุยในชุมชนของเรา!\n"
                "ถ้าคุณมีคำถามหรือปัญหา สอบถามได้ที่ <#1281566308097462335>\n"
                "หากต้องการเข้าร่วม สามารถกรอกใบสมัครได้ที่ <#1349726875030913085>"
          
            )
            await member.send(welcome_message)
            print(f"✅ ส่งข้อความต้อนรับไปยัง {member.name} สำเร็จ")
        except discord.Forbidden:
            print(f"❌ ไม่สามารถส่งข้อความต้อนรับไปยัง {member.name} (สมาชิกอาจปิดการรับ DM)")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Event: ส่งข้อความ DM ไปยังสมาชิกที่ออกจากเซิร์ฟเวอร์
        """
        try:
            # ข้อความ DM ที่จะส่งไปยังสมาชิกที่ออกจากเซิร์ฟเวอร์
            goodbye_message = (
                f"สวัสดี {member.name},\n"
                "เราสังเกตว่าคุณได้ออกจากเซิร์ฟเวอร์ของเราแล้ว 😢\n"
                "หากมีข้อเสนอแนะหรือคำถามใด ๆ โปรดแจ้งให้เราทราบ เรายินดีต้อนรับคุณกลับมาเสมอ!\n"
                "หากคุณต้องการกลับมา Join our Discord : https://discord.gg/277nRyGhmq\n"
                "ขอให้คุณโชคดีในทุกสิ่งที่ทำ! 🎉"
            )
            await member.send(goodbye_message)
            print(f"✅ ส่งข้อความ DM ลาให้กับ {member.name} สำเร็จ")
        except discord.Forbidden:
            # หากไม่สามารถส่ง DM ได้ (เช่น สมาชิกปิดการรับ DM)
            print(f"❌ ไม่สามารถส่งข้อความ DM ลาให้กับ {member.name} (สมาชิกอาจปิดการรับ DM)")

async def setup(bot):
    """
    ฟังก์ชันสำหรับเพิ่ม Cog นี้ในบอท
    """
    await bot.add_cog(AutoRole(bot))