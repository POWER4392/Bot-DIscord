import discord
from discord.ext import commands
import asyncio
import datetime
import json
import random
import string
from core.shared import config, config_file
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

        # Lấy danh sách ID câu hỏi cụ thể (nếu có) hoặc lấy ngẫu nhiên
        question_count = int(server_cfg.get("verify_question_count", 1))
        pinned_ids = server_cfg.get("verify_question_ids", [])

        def get_questions():
            with db_lock:
                if pinned_ids:
                    # Lấy đúng các câu hỏi được chỉ định, giữ nguyên thứ tự ngẫu nhiên
                    placeholders = ",".join(["?"] * len(pinned_ids))
                    cursor.execute(
                        f"SELECT question, option_a, option_b, option_c, option_d, correct_option "
                        f"FROM quiz_questions WHERE guild_id = ? AND id IN ({placeholders}) ORDER BY random()",
                        [guild_id] + list(pinned_ids)
                    )
                else:
                    # Lấy ngẫu nhiên theo số lượng đã cấu hình
                    cursor.execute(
                        "SELECT question, option_a, option_b, option_c, option_d, correct_option "
                        "FROM quiz_questions WHERE guild_id = ? ORDER BY random() LIMIT ?",
                        (guild_id, question_count)
                    )
                return cursor.fetchall()

        try:
            rows = get_questions()
        except Exception as e:
            print(f"[Verification] Lỗi truy vấn câu hỏi: {e}")
            rows = []

        if rows:
            actual_count = len(rows)
            for idx, row in enumerate(rows):
                q_text, opt_a, opt_b, opt_c, opt_d, correct_opt = row
                code = correct_opt.strip().upper()

                embed = discord.Embed(
                    title=f"🔒 Xác Minh Tài Khoản ({idx + 1}/{actual_count})",
                    description=(
                        f"Để chứng minh bạn không phải bot, hãy trả lời câu hỏi sau:\n\n"
                        f"**{q_text}**\n\n"
                        f"🇦 {opt_a}\n"
                        f"🇧 {opt_b}\n"
                        f"🇨 {opt_c}\n"
                        f"🇩 {opt_d}\n\n"
                        f"Nhập đáp án của bạn (chọn **A, B, C, hoặc D**) vào chat trong kênh này trong vòng **60 giây**."
                    ),
                    color=0x5865F2
                )
                embed.set_footer(text="Chỉ mình bạn thấy thông báo này.")

                if idx == 0:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.edit_original_response(embed=embed)

                def check(m):
                    return (
                        m.author.id == member.id
                        and m.channel == interaction.channel
                    )

                try:
                    msg = await interaction.client.wait_for("message", check=check, timeout=60.0)
                    try:
                        await msg.delete()
                    except:
                        pass
                    if msg.content.strip().upper() != code:
                        fail_embed = discord.Embed(
                            title="❌ Sai Đáp Án",
                            description="Bạn đã trả lời sai đáp án. Nhấn nút để bắt đầu xác minh lại từ đầu.",
                            color=0xED4245
                        )
                        await interaction.followup.send(embed=fail_embed, ephemeral=True)
                        return
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        title="⏰ Hết Giờ",
                        description="Bạn đã không trả lời trong vòng 60 giây. Nhấn nút để thử lại.",
                        color=0xED4245
                    )
                    await interaction.followup.send(embed=timeout_embed, ephemeral=True)
                    return
        else:
            # Fallback to Math CAPTCHAs
            actual_count = question_count
            for idx in range(actual_count):
                a, b = random.randint(1, 9), random.randint(1, 9)
                answer = a + b
                code = str(answer)

                embed = discord.Embed(
                    title=f"🔒 Xác Minh Tài Khoản ({idx + 1}/{actual_count})",
                    description=(
                        f"Để chứng minh bạn không phải bot, hãy trả lời câu hỏi sau:\n\n"
                        f"**{a} + {b} = ?**\n\n"
                        f"Nhập đáp án vào chat trong kênh này trong vòng **60 giây**."
                    ),
                    color=0x5865F2
                )
                embed.set_footer(text="Chỉ mình bạn thấy thông báo này.")

                if idx == 0:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.edit_original_response(embed=embed)

                def check(m):
                    return (
                        m.author.id == member.id
                        and m.channel == interaction.channel
                    )

                try:
                    msg = await interaction.client.wait_for("message", check=check, timeout=60.0)
                    try:
                        await msg.delete()
                    except:
                        pass
                    if msg.content.strip() != code:
                        fail_embed = discord.Embed(
                            title="❌ Sai Đáp Án",
                            description="Bạn đã trả lời sai đáp án. Nhấn nút để bắt đầu xác minh lại từ đầu.",
                            color=0xED4245
                        )
                        await interaction.followup.send(embed=fail_embed, ephemeral=True)
                        return
                except asyncio.TimeoutError:
                    timeout_embed = discord.Embed(
                        title="⏰ Hết Giờ",
                        description="Bạn đã không trả lời trong vòng 60 giây. Nhấn nút để thử lại.",
                        color=0xED4245
                    )
                    await interaction.followup.send(embed=timeout_embed, ephemeral=True)
                    return

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
        await interaction.edit_original_response(embed=success_embed)


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

    # ── Lệnh xem danh sách câu hỏi verify ────
    @commands.hybrid_command(
        name="verify_questions",
        description="Xem toàn bộ câu hỏi verify có trong máy chủ (kèm ID)."
    )
    @commands.guild_only()  # Điều kiện A: chỉ dùng trong server
    @is_mod()
    async def verify_questions(self, ctx):
        """Liệt kê tất cả câu hỏi trong DB của server, hiển thị ID để dùng với /set_verify_questions."""
        guild_id = str(ctx.guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)

        # Điều kiện B: chỉ dùng trong verify_channel (nếu đã cấu hình)
        verify_channel_id = server_cfg.get("verify_channel_id")
        if verify_channel_id and ctx.channel.id != int(verify_channel_id):
            verify_ch = ctx.guild.get_channel(int(verify_channel_id))
            mention = verify_ch.mention if verify_ch else f"<#{verify_channel_id}>"
            return await ctx.send(
                f"❌ Lệnh này chỉ được dùng trong kênh verify: {mention}",
                ephemeral=True
            )

        def fetch_all():
            with db_lock:
                cursor.execute(
                    "SELECT id, question, correct_option FROM quiz_questions WHERE guild_id = ? ORDER BY id",
                    (guild_id,)
                )
                return cursor.fetchall()

        rows = await self.bot.loop.run_in_executor(None, fetch_all)

        if not rows:
            return await ctx.send(
                "❌ Chưa có câu hỏi nào. Thêm câu hỏi qua **GUI Quản Lý** trước nhé!",
                ephemeral=True
            )

        pinned_ids = server_cfg.get("verify_question_ids", [])
        mode_text = (
            f"🎯 **Đang dùng câu hỏi cụ thể:** ID {', '.join(str(i) for i in pinned_ids)}"
            if pinned_ids
            else "🎲 **Chế độ hiện tại: Ngẫu nhiên** (dùng `/set_verify_questions` để chọn cụ thể)"
        )

        lines = []
        for q_id, q_text, correct in rows:
            marker = "✅" if (not pinned_ids or q_id in pinned_ids) else "⬜"
            short = q_text[:60] + "..." if len(q_text) > 60 else q_text
            lines.append(f"{marker} **[ID: {q_id}]** {short} *(Đáp án: {correct})*")

        # Chia trang nếu nhiều câu hỏi
        chunks, page = [], []
        for line in lines:
            page.append(line)
            if len(page) >= 10:
                chunks.append(page)
                page = []
        if page:
            chunks.append(page)

        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"📋 Danh Sách Câu Hỏi Verify ({i+1}/{len(chunks)})",
                description=mode_text + "\n\n" + "\n".join(chunk),
                color=0x5865F2
            )
            embed.set_footer(text=f"Tổng: {len(rows)} câu hỏi • Dùng /set_verify_questions để cấu hình")
            await ctx.send(embed=embed, ephemeral=True)

    # ── Lệnh cấu hình câu hỏi verify cụ thể ──
    @commands.hybrid_command(
        name="set_verify_questions",
        description="Chọn câu hỏi cụ thể hoặc ngẫu nhiên cho bước xác minh."
    )
    @commands.guild_only()  # Điều kiện A: chỉ dùng trong server
    @is_mod()
    async def set_verify_questions(
        self,
        ctx,
        ids: str = None
    ):
        """
        Chọn câu hỏi cho verify theo ID.
        - ids: danh sách ID cách nhau bằng dấu phẩy, VD: "1,3,5"
        - Để trống (bỏ qua tham số) → về chế độ ngẫu nhiên
        """
        guild_id = str(ctx.guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)

        # Điều kiện B: chỉ dùng trong verify_channel (nếu đã cấu hình)
        verify_channel_id = server_cfg.get("verify_channel_id")
        if verify_channel_id and ctx.channel.id != int(verify_channel_id):
            verify_ch = ctx.guild.get_channel(int(verify_channel_id))
            mention = verify_ch.mention if verify_ch else f"<#{verify_channel_id}>"
            return await ctx.send(
                f"❌ Lệnh này chỉ được dùng trong kênh verify: {mention}",
                ephemeral=True
            )

        # Điều kiện C: phải có câu hỏi trong DB trước khi cho chọn cụ thể
        if ids:
            def check_has_questions():
                with db_lock:
                    cursor.execute(
                        "SELECT COUNT(*) FROM quiz_questions WHERE guild_id = ?",
                        (guild_id,)
                    )
                    return cursor.fetchone()[0]

            total = await self.bot.loop.run_in_executor(None, check_has_questions)
            if total == 0:
                return await ctx.send(
                    "❌ Máy chủ chưa có câu hỏi nào trong ngân hàng.\n"
                    "Hãy thêm câu hỏi qua **GUI Quản Lý** trước, sau đó dùng `/verify_questions` để xem ID.",
                    ephemeral=True
                )

        # Parse danh sách ID
        if ids:
            try:
                id_list = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
            except Exception:
                return await ctx.send("❌ Định dạng không hợp lệ. Hãy nhập danh sách ID cách nhau bằng dấu phẩy, VD: `1,3,5`", ephemeral=True)

            if not id_list:
                return await ctx.send("❌ Không tìm thấy ID hợp lệ nào.", ephemeral=True)

            # Kiểm tra các ID có tồn tại trong DB không
            def validate_ids():
                with db_lock:
                    placeholders = ",".join(["?"] * len(id_list))
                    cursor.execute(
                        f"SELECT id FROM quiz_questions WHERE guild_id = ? AND id IN ({placeholders})",
                        [guild_id] + id_list
                    )
                    return [r[0] for r in cursor.fetchall()]

            valid_ids = await self.bot.loop.run_in_executor(None, validate_ids)
            invalid = [i for i in id_list if i not in valid_ids]

            if invalid:
                return await ctx.send(
                    f"❌ Các ID sau không tồn tại trong máy chủ: **{', '.join(str(i) for i in invalid)}**\n"
                    f"Dùng `/verify_questions` để xem danh sách ID hợp lệ.",
                    ephemeral=True
                )
        else:
            id_list = []  # Về chế độ ngẫu nhiên

        # Lưu vào config
        if "servers" not in config:
            config["servers"] = {}
        if guild_id not in config["servers"]:
            config["servers"][guild_id] = {}

        config["servers"][guild_id]["verify_question_ids"] = id_list

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            return await ctx.send(f"❌ Không thể lưu cấu hình: {e}", ephemeral=True)

        if id_list:
            embed = discord.Embed(
                title="✅ Đã Cấu Hình Câu Hỏi Verify",
                description=(
                    f"🎯 Bot sẽ hỏi **{len(id_list)} câu hỏi cụ thể** sau:\n\n"
                    + "\n".join(f"• ID **{i}**" for i in id_list)
                    + f"\n\nMỗi lần verify, {len(id_list)} câu này sẽ được hỏi theo thứ tự ngẫu nhiên."
                ),
                color=0x57F287
            )
        else:
            embed = discord.Embed(
                title="✅ Về Chế Độ Ngẫu Nhiên",
                description=(
                    f"🎲 Bot sẽ lấy ngẫu nhiên **{server_cfg.get('verify_question_count', 1)} câu hỏi** "
                    f"từ toàn bộ ngân hàng câu hỏi mỗi lần verify."
                ),
                color=0x57F287
            )
        embed.set_footer(text="Dùng /verify_questions để xem danh sách câu hỏi kèm ID.")
        await ctx.send(embed=embed, ephemeral=True)

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
