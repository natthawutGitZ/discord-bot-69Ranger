import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz

# กำหนดเขตเวลาไทย
THAI_TZ = pytz.timezone("Asia/Bangkok")

class EventManager(commands.Cog):
    """
    Cog สำหรับจัดการกิจกรรมในเซิร์ฟเวอร์
    """
    def __init__(self, bot):
        self.bot = bot
        self.events = {}  # เก็บข้อมูลกิจกรรมในรูปแบบ {event_id: event_data}
        self.countdown_task.start()  # เริ่ม Task สำหรับนับถอยหลัง

    def cog_unload(self):
        """
        หยุด Task เมื่อ Cog ถูกปิด
        """
        self.countdown_task.cancel()

    # ========================= TASK =========================
    @tasks.loop(minutes=1)
    async def countdown_task(self):
        """
        Task สำหรับอัปเดตข้อความ "เหลืออีก..." ทุก 1 นาที
        """
        now = datetime.now(THAI_TZ)
        for event_id, event in self.events.items():
            event_time = datetime.strptime(f"{event['date']} {event['time']}", "%d-%m-%Y %H:%M").replace(tzinfo=THAI_TZ)
            remaining = event_time - now

            if remaining.total_seconds() <= 0:
                # หากกิจกรรมเริ่มแล้ว
                continue

            # อัปเดตข้อความ "เหลืออีก..."
            channel = event["channel"]
            message = event["message"]
            embed = self.generate_event_embed(event_id)
            await message.edit(embed=embed)

    # ========================= COMMANDS =========================
    @commands.command(name="event_create", description="สร้างกิจกรรมใหม่")
    async def event_create(self, interaction: discord.Interaction, name: str, date: str, time: str, max_participants: int, description: str):
        """
        คำสั่งสำหรับสร้างกิจกรรมใหม่
        """
        event_id = f"EV{len(self.events) + 1:03}"  # สร้าง Event ID เช่น EV001
        event_time = datetime.strptime(f"{date} {time}", "%d-%m-%Y %H:%M").replace(tzinfo=THAI_TZ)

        if event_time <= datetime.now(THAI_TZ):
            await interaction.response.send_message("❌ ไม่สามารถสร้างกิจกรรมในอดีตได้", ephemeral=True)
            return

        self.events[event_id] = {
            "name": name,
            "date": date,
            "time": time,
            "max_participants": max_participants,
            "description": description,
            "participants": {"yes": [], "no": [], "maybe": []},
            "created_by": interaction.user,
            "channel": interaction.channel,
            "message": None
        }

        embed = self.generate_event_embed(event_id)
        view = EventView(self, event_id)

        message = await interaction.response.send_message(embed=embed, view=view)
        self.events[event_id]["message"] = await message.original_response()

    # ========================= HELPERS =========================
    def generate_event_embed(self, event_id):
        """
        สร้าง Embed สำหรับแสดงข้อมูลกิจกรรม
        """
        event = self.events[event_id]
        now = datetime.now(THAI_TZ)
        event_time = datetime.strptime(f"{event['date']} {event['time']}", "%d-%m-%Y %H:%M").replace(tzinfo=THAI_TZ)
        remaining = event_time - now

        embed = discord.Embed(
            title=f"**[{event_id}] {event['name']}**",
            description=event["description"],
            color=discord.Color.blue()
        )
        embed.add_field(name="📅 วันเวลา", value=f"{event['date']} | เวลา {event['time']}", inline=False)
        embed.add_field(name="⏳ เหลืออีก", value=f"{remaining.days} วัน {remaining.seconds // 3600} ชั่วโมง", inline=False)
        embed.add_field(name="👥 จำนวนที่รับ", value=f"{len(event['participants']['yes'])} / {event['max_participants']} คน", inline=False)
        embed.add_field(
            name="✅ เข้าร่วม | ❌ ไม่เข้าร่วม | 🔄 อาจจะเข้าร่วม",
            value=(
                f"{', '.join([f'@{p.display_name}' for p in event['participants']['yes']]) or 'ไม่มี'} | "
                f"{', '.join([f'@{p.display_name}' for p in event['participants']['no']]) or 'ไม่มี'} | "
                f"{', '.join([f'@{p.display_name}' for p in event['participants']['maybe']]) or 'ไม่มี'}"
            ),
            inline=False
        )
        embed.set_footer(text=f"จัดโดย: {event['created_by'].display_name}")
        return embed

class EventView(discord.ui.View):
    """
    View สำหรับปุ่มโต้ตอบในกิจกรรม
    """
    def __init__(self, cog, event_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.event_id = event_id

    @discord.ui.button(label="✅ เข้าร่วม", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_participation(interaction, "yes")

    @discord.ui.button(label="❌ ไม่เข้าร่วม", style=discord.ButtonStyle.red)
    async def not_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_participation(interaction, "no")

    @discord.ui.button(label="🔄 อาจจะเข้าร่วม", style=discord.ButtonStyle.blurple)
    async def maybe_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_participation(interaction, "maybe")

    async def update_participation(self, interaction: discord.Interaction, status: str):
        """
        อัปเดตรายชื่อผู้เข้าร่วมในสถานะที่เลือก
        """
        event = self.cog.events[self.event_id]
        user = interaction.user

        # ลบผู้ใช้จากสถานะอื่นก่อน
        for key in event["participants"]:
            if user in event["participants"][key]:
                event["participants"][key].remove(user)

        # ตรวจสอบจำนวนผู้เข้าร่วม
        if status == "yes" and len(event["participants"]["yes"]) >= event["max_participants"]:
            await interaction.response.send_message("❌ จำนวนผู้เข้าร่วมเต็มแล้ว", ephemeral=True)
            return

        # เพิ่มผู้ใช้ในสถานะที่เลือก
        event["participants"][status].append(user)

        # อัปเดต Embed
        embed = self.cog.generate_event_embed(self.event_id)
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    """
    ฟังก์ชันสำหรับเพิ่ม Cog นี้ในบอท
    """
    await bot.add_cog(EventManager(bot))