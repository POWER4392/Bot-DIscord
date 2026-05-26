import discord
from discord.ext import commands
import asyncio
import datetime
import random
import string
from core.shared import config
from core.database import cursor, conn, db_lock


def is_mod():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator: return True
        guild_id = str(ctx.guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)
        mod_role_ids = server_cfg.get("mod_role_ids", [])
        old_mod = server_cfg.get("mod_role_id")
        if old_mod and str(old_mod) not in [str(x) for x in mod_role_ids]:
            mod_role_ids = list(mod_role_ids) + [old_mod]
        if not mod_role_ids: return False
        user_role_ids = [r.id for r in ctx.author.roles]
        return any(int(m) in user_role_ids for m in mod_role_ids)
    return commands.check(predicate)


# ─────────────────────────────────────────────
#  Verification View  (Button CAPTCHA)
# ─────────────────────────────────────────────

class VerificationView(discord.ui.View):
    """Persistent view – survives bot restarts."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Xác Minh Tôi Là Người Thật",
        style=discord.ButtonStyle.success,
        custom_id="verify_human_btn"
    )
    async def verify_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        guild_id = str(guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)

        # Check if already verified (has auto_role)
        auto_role_id = server_cfg.get("auto_role_id")
        if auto_role_id:
            auto_role = guild.get_role(int(auto_role_id))
            if auto_role and auto_role in member.roles:
                return await interaction.response.send_message(
                    "✅ Bạn đã được xác minh rồi!", ephemeral=True
                )

        # Send math CAPTCHA as follow-up
        a, b = random.randint(1, 9), random.randint(1, 9)
        answer = a + b
        code = str(answer)

        embed = discord.Embed(
            title="🔒 Xác Minh Tài Khoản",
            description=(
                f"Để chứng minh bạn không phải bot, hãy trả lời câu hỏi sau:\n\n"
                f"**{a} + {b} = ?**\n\n"
                f"Nhập đáp án vào chat trong kênh này trong vòng **60 giây**."
            ),
            color=0x5865F2
        )
        embed.set_footer(text="Chỉ mình bạn thấy thông báo này.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        def check(m):
            return (
                m.author.id == member.id
                and m.channel == interaction.channel
                and m.content.strip() == code
            )

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=60.0)
            try:
                await msg.delete()
            except Exception:
                pass

            # Grant auto-role
            roles_granted = []
            if auto_role_id:
                auto_role = guild.get_role(int(auto_role_id))
                if auto_role:
                    try:
                        await member.add_roles(auto_role, reason="Xác minh thành công")
                        roles_granted.append(auto_role.name)
                    except discord.Forbidden:
                        pass

            # Also remove a "pending" / "unverified" role if configured
            pending_role_id = server_cfg.get("pending_role_id")
            if pending_role_id:
                pending_role = guild.get_role(int(pending_role_id))
                if pending_role and pending_role in member.roles:
                    try:
                        await member.remove_roles(pending_role, reason="Đã xác minh")
                    except Exception:
                        pass

            success_embed = discord.Embed(
                title="🎉 Xác Minh Thành Công!",
                description=(
                    f"Chào mừng **{member.display_name}** vào server!\n"
                    + (f"Bạn đã được cấp vai trò: **{', '.join(roles_granted)}**" if roles_granted else "")
                ),
                color=0x57F287
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)

        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Hết Giờ",
                description="Bạn đã không trả lời trong 60 giây. Nhấn nút lại để thử lần khác.",
                color=0xED4245
            )
            await interaction.followup.send(embed=timeout_embed, ephemeral=True)


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

        # 1. Auto-role (cấp ngay nếu KHÔNG cần xác minh; hoặc cấp role "chờ xác minh")
        pending_role_id = server_cfg.get("pending_role_id")
        auto_role_id    = server_cfg.get("auto_role_id")

        if pending_role_id:
            # Chế độ xác minh: cấp role "chờ" trước
            pending_role = guild.get_role(int(pending_role_id))
            if pending_role:
                try:
                    await member.add_roles(pending_role, reason="Thành viên mới – chờ xác minh")
                except discord.Forbidden:
                    pass
        else:
            # Không có xác minh → cấp thẳng auto-role
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

        # Nếu có xác minh → kèm nút verify
        if pending_role_id:
            verify_channel_id = server_cfg.get("verify_channel_id")
            if verify_channel_id:
                verify_ch = guild.get_channel(int(verify_channel_id))
                if verify_ch:
                    embed.add_field(
                        name="🔒 Xác Minh",
                        value=f"Vui lòng vào {verify_ch.mention} và nhấn nút **Xác Minh** để mở khoá server!",
                        inline=False
                    )
            embed.set_footer(text="Hãy xác minh để được truy cập đầy đủ server.")
        else:
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

    # ── Lệnh setup hệ thống xác minh ─────────
    @commands.hybrid_command(
        name="setup_verify",
        description="Tạo panel xác minh (button) cho thành viên mới."
    )
    @is_mod()
    async def setup_verify(self, ctx, channel: discord.TextChannel = None):
        """Gửi panel xác minh vào kênh chỉ định (mặc định: kênh hiện tại)."""
        channel = channel or ctx.channel

        embed = discord.Embed(
            title="🔐 XÁC MINH THÀNH VIÊN",
            description=(
                "Chào mừng bạn đến với **{}**!\n\n"
                "Để bảo vệ cộng đồng khỏi bot & tài khoản ảo, bạn cần vượt qua bước xác minh nhanh.\n\n"
                "👇 Nhấn nút bên dưới, trả lời câu hỏi nhỏ và thế là xong!"
            ).format(ctx.guild.name),
            color=0x5865F2
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
        embed.set_footer(text="Quá trình xác minh chỉ mất vài giây • Thông tin của bạn được bảo mật.")

        view = VerificationView()
        await channel.send(embed=embed, view=view)
        await ctx.send(f"✅ Panel xác minh đã được tạo tại {channel.mention}!", ephemeral=True)

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
