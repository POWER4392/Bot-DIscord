import discord
from discord.ext import commands
import asyncio
import datetime
import json
import random
import string
from core.shared import config, config_file, is_mod
from core.database import cursor, conn, db_lock


# ─────────────────────────────────────────────
#  Welcome Cog
# ─────────────────────────────────────────────

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── on_member_join ────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        guild_id = str(guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)

        # 1. Auto-role (cấp ngay)
        auto_role_id = server_cfg.get("auto_role_id")
        if auto_role_id:
            auto_role = guild.get_role(int(auto_role_id))
            if auto_role:
                try:
                    await member.add_roles(auto_role, reason="Auto-role thành viên mới")
                except discord.Forbidden:
                    print(f"[Welcome] Không đủ quyền cấp role {auto_role.name} cho {member}")

        # 2. Gửi chào mừng vào welcome_channel
        welcome_channel_id = server_cfg.get("welcome_channel_id")
        if not welcome_channel_id:
            return

        channel = guild.get_channel(int(welcome_channel_id))
        if not channel:
            return

        raw_msg = server_cfg.get(
            "welcome_message",
            "Chào mừng {mention} đã gia nhập server! Đọc luật rồi quẩy nhé!"
        )
        welcome_text = (
            raw_msg
            .replace("{mention}", member.mention)
            .replace("{name}", member.display_name)
            .replace("{server}", guild.name)
            .replace("{count}", str(guild.member_count))
        )

        embed = discord.Embed(
            title=f"👋 Chào Mừng Thành Viên Mới!",
            description=welcome_text,
            color=0x5865F2,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📛 Tên", value=member.mention, inline=True)
        embed.add_field(name="📅 Tài Khoản Tạo", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="👥 Thành Viên Thứ", value=f"**#{guild.member_count}**", inline=True)

        embed.set_footer(text=f"{guild.name} • Chúc bạn có những phút giây vui vẻ!")

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            print(f"[Welcome] Không có quyền gửi tin vào kênh welcome {channel.name}")

    # ── on_member_remove ──────────────────────
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        guild_id = str(guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)

        welcome_channel_id = server_cfg.get("welcome_channel_id")
        if not welcome_channel_id:
            return
        channel = guild.get_channel(int(welcome_channel_id))
        if not channel:
            return

        raw_msg = server_cfg.get("leave_message", "{name} đã rời cuộc chơi. Cay!")
        leave_text = (
            raw_msg
            .replace("{mention}", member.mention)
            .replace("{name}", member.display_name)
            .replace("{server}", guild.name)
        )

        embed = discord.Embed(
            description=f"🚪 {leave_text}",
            color=0xED4245,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Còn lại: {guild.member_count} thành viên")
        try:
            await channel.send(embed=embed)
        except Exception:
            pass

    # ── Lệnh test chào mừng ───────────────────
    @commands.hybrid_command(
        name="test_welcome",
        description="Kiểm tra tin nhắn chào mừng (chỉ Mod/Admin)."
    )
    @is_mod()
    async def test_welcome(self, ctx):
        await self.on_member_join(ctx.author)
        await ctx.send("✅ Đã thử kích hoạt sự kiện chào mừng cho bạn!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
