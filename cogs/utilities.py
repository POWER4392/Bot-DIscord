import discord
from discord.ext import commands
import asyncio
import datetime
import json
from core.shared import config, temp_voices
from core.database import cursor, conn, db_lock

class TicketControlView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Khoá & Khắc Phục", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "ticket-" in interaction.channel.name:
            await interaction.response.send_message("🔒 Vé hỗ trợ này sẽ bị rã đông và xoá sau 5 giây...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else: await interaction.response.send_message("❌ Kênh này không phải vé hỗ trợ.", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Tạo Vé Hỗ Trợ Mới", style=discord.ButtonStyle.success, emoji="🎫", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild, user = interaction.guild, interaction.user
        if discord.utils.get(guild.channels, name=f"ticket-{user.name.lower()}"):
            return await interaction.response.send_message(f"❌ Bạn đã có một vé hỗ trợ đang mở rồi!", ephemeral=True)
        
        overwrites = { 
            guild.default_role: discord.PermissionOverwrite(read_messages=False), 
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True), 
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True) 
        }
        
        server_cfg = config.get("servers", {}).get(str(guild.id), config)
        mod_role_ids = server_cfg.get("mod_role_ids", [])
        old_mod_role_id = server_cfg.get("mod_role_id")
        if old_mod_role_id and old_mod_role_id not in mod_role_ids: 
            mod_role_ids.append(old_mod_role_id)
            
        for m_id in mod_role_ids:
            role = guild.get_role(int(m_id))
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        category = discord.utils.get(guild.categories, name="HỖ TRỢ (TICKETS)")
        if not category: category = await guild.create_category("HỖ TRỢ (TICKETS)")
        ticket_channel = await guild.create_text_channel(f"ticket-{user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(title="🎫 Kênh Hỗ Trợ Độc Quyền", description=f"Xin chào {user.mention}! Vui lòng mô tả vấn đề của bạn ở đây.\nĐội ngũ Ban Quản Trị sẽ phản hồi sớm nhất có thể.", color=0x5865F2)
        await ticket_channel.send(content=f"{user.mention}", embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ Vé của bạn đã được tạo tại {ticket_channel.mention}", ephemeral=True)

class VoiceNameModal(discord.ui.Modal, title="Đăng Ký Khởi Tạo Phòng Thoại"):
    room_name = discord.ui.TextInput(
        label="Nhập Tên Phòng Bạn Muốn:",
        placeholder="VD: Hội chém gió, Tìm Party Rank...",
        min_length=2, max_length=50
    )
    user_limit = discord.ui.TextInput(
        label="Số người tối đa (bỏ trống = không giới hạn):",
        placeholder="VD: 5, 10...",
        required=False, max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        server_cfg = config.get("servers", {}).get(str(guild.id), config)
        category_id = server_cfg.get("voice_category_id")
        if category_id: category = guild.get_channel(int(category_id))
        else: category = discord.utils.get(guild.categories, name="TRẠM DỪNG CHÂN")
        
        if not category: category = await guild.create_category("TRẠM DỪNG CHÂN")
        
        limit = 0
        if self.user_limit.value.isdigit():
            limit = int(self.user_limit.value)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True),
            interaction.user: discord.PermissionOverwrite(manage_channels=True, connect=True)
        }
        
        new_channel = await guild.create_voice_channel(
            name=f"🎧 {self.room_name.value}",
            category=category,
            overwrites=overwrites,
            user_limit=limit
        )
        temp_voices.add(new_channel.id)
        
        await interaction.response.send_message(
            f"✅ Bùm! Phòng của bạn đã được đắp lên: {new_channel.mention}\n"
            f"*(Bạn được cấp full quyền Sửa Tên & Khoá Kênh. Kênh sẽ tự động xoá khi không còn ai.)*",
            ephemeral=True
        )

class VoiceGeneratorView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Tạo Kênh Thoại Mới", style=discord.ButtonStyle.primary, emoji="🎙️", custom_id="btn_create_voice")
    async def create_voice_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VoiceNameModal())

class RoleButton(discord.ui.Button):
    def __init__(self, role_dict, custom_id_suffix):
        self.role_id = int(role_dict["id"])
        self.role_name = role_dict["name"]
        super().__init__(label=self.role_name, style=discord.ButtonStyle.secondary, custom_id=f"btn_role_{self.role_id}_{custom_id_suffix}")

    async def callback(self, interaction: discord.Interaction):
        guild, member = interaction.guild, interaction.user
        role = guild.get_role(self.role_id)
        if not role:
            return await interaction.response.send_message("❌ Vai trò này không còn khả dụng trên máy chủ.", ephemeral=True)
            
        if role in member.roles:
            try:
                await member.remove_roles(role)
                await interaction.response.send_message(f"✅ Đã gỡ bỏ vai trò **{self.role_name}**.", ephemeral=True)
            except discord.errors.Forbidden:
                await interaction.response.send_message("❌ Bot không đủ quyền để gỡ vai trò này.", ephemeral=True)
        else:
            try:
                await member.add_roles(role)
                await interaction.response.send_message(f"✅ Đã cấp phát vai trò **{self.role_name}**.", ephemeral=True)
            except discord.errors.Forbidden:
                await interaction.response.send_message("❌ Bot không đủ quyền để cấp vai trò này.", ephemeral=True)

class PersistentRoleView(discord.ui.View):
    def __init__(self, roles_data, custom_id):
        super().__init__(timeout=None)
        for r in roles_data:
            self.add_item(RoleButton(r, custom_id))


class QuizAnswerButton(discord.ui.Button):
    def __init__(self, label, custom_id, correct_option):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)
        self.correct_option = correct_option

    async def callback(self, interaction: discord.Interaction):
        choice = self.custom_id.split("_")[-1]
        if choice == self.correct_option:
            await interaction.response.send_message(f"🎉 **Chính xác!** Bạn đã chọn đáp án **{choice}** là đáp án đúng.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ **Sai rồi!** Đáp án **{choice}** không chính xác. Hãy thử lại nhé!", ephemeral=True)


class QuizView(discord.ui.View):
    def __init__(self, question_id, correct_option):
        super().__init__(timeout=60)
        for choice in ["A", "B", "C", "D"]:
            self.add_item(QuizAnswerButton(label=choice, custom_id=f"quiz_{question_id}_{choice}", correct_option=correct_option))


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


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return
        
        if after.channel:
            guild = member.guild
            server_cfg = config.get("servers", {}).get(str(guild.id), config)
            trigger_name = server_cfg.get("voice_trigger_name", "➕ Bấm Tạo Phòng")
            if after.channel.name == trigger_name:
                category = after.channel.category
                new_channel = await guild.create_voice_channel(name=f"🎧 Phòng của {member.display_name}", category=category)
                temp_voices.add(new_channel.id)
                try: await member.move_to(new_channel)
                except: pass
            
        # Xóa kênh tạm ngay khi kênh trống hoàn toàn (không có timer 60s)
        if before.channel and before.channel.id in temp_voices:
            if len(before.channel.members) == 0:
                try:
                    chan = self.bot.get_channel(before.channel.id)
                    if chan and len(chan.members) == 0:
                        await chan.delete()
                        temp_voices.discard(before.channel.id)
                except Exception:
                    pass

    @commands.hybrid_command(name=config.get("cmd_ticket_setup", "ticket_setup") or "ticket_setup")
    @is_mod()
    async def ticket_setup(self, ctx):
        embed = discord.Embed(
            title="🎫 TRUNG TÂM HỖ TRỢ CHIẾN LƯỢC",
            description="Bạn có vấn đề cần giải quyết, muốn khiếu nại hoặc đóng góp ý kiến?\nVui lòng ấn vào nút bên dưới để mở một Phiên Hỗ Trợ bí mật cùng Ban Quản Trị.",
            color=0x2B2D31
        )
        if ctx.guild.icon: embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed, view=TicketView())

    @commands.hybrid_command(name="setup_roles", description="Tạo một bảng Chọn Vai Trò (Tối đa 5 vai trò)")
    @is_mod()
    async def setup_roles(self, ctx, title: str, r1: discord.Role, r2: discord.Role=None, r3: discord.Role=None, r4: discord.Role=None, r5: discord.Role=None):
        roles = [r for r in [r1, r2, r3, r4, r5] if r]
        roles_data = [{"id": str(r.id), "name": r.name} for r in roles]
        
        embed = discord.Embed(title=title, description="Sử dụng Menu bên dưới để tự Cấp/Gỡ vai trò cho bản thân nhé!", color=0x3498DB)
        panel_id = str(int(datetime.datetime.now().timestamp() * 1000))
        custom_id = f"rr_panel_{panel_id}"
        view = PersistentRoleView(roles_data, custom_id)
        
        await ctx.send(embed=embed, view=view)
        
        with db_lock:
            cursor.execute("INSERT INTO reaction_panels (message_id, guild_id, roles_json) VALUES (?, ?, ?)", 
                           (panel_id, str(ctx.guild.id), json.dumps(roles_data)))
            conn.commit()

    @commands.hybrid_command(name=config.get("cmd_setup_voice", "setup_voice") or "setup_voice")
    @is_mod()
    async def setup_voice(self, ctx):
        guild = ctx.guild
        server_cfg = config.get("servers", {}).get(str(guild.id), config)
        category_id = server_cfg.get("voice_category_id")
        if category_id: category = guild.get_channel(int(category_id))
        else: category = discord.utils.get(guild.categories, name="TRẠM DỪNG CHÂN")
        
        if not category: category = await guild.create_category("TRẠM DỪNG CHÂN")
        
        trigger_name = server_cfg.get("voice_trigger_name", "➕ Bấm Tạo Phòng")
        trigger_channel = discord.utils.get(guild.voice_channels, name=trigger_name)
        if not trigger_channel:
            trigger_channel = await guild.create_voice_channel(name=trigger_name, category=category)
        
        embed = discord.Embed(title="🎙️ BỘ ĐIỀU KHIỂN PHÒNG THOẠI", description=f"Kênh mồi **{trigger_channel.mention}** đã được kích hoạt!\n\nBạn có thể vào thẳng kênh mồi để hệ thống tự cấp 1 phòng, hoặc bấm nút dưới đây để tạo một phòng theo ý muốn.", color=0x5865F2)
        await ctx.send(embed=embed, view=VoiceGeneratorView())

    @commands.hybrid_command(name="myvoice")
    async def user_create_voice(self, ctx, limit: int = 0, *, room_name: str = None):
        guild, user = ctx.guild, ctx.author
        if not user.voice or not user.voice.channel:
            return await ctx.send("❌ Bạn cần vào một kênh thoại bất kỳ trước để dùng lệnh này!")
        
        server_cfg = config.get("servers", {}).get(str(guild.id), config)
        category_id = server_cfg.get("voice_category_id")
        if category_id: category = guild.get_channel(int(category_id))
        else: category = discord.utils.get(guild.categories, name="TRẠM DỪNG CHÂN")
        if not category: category = await guild.create_category("TRẠM DỪNG CHÂN")
        
        if not room_name: room_name = f"Phòng của {user.display_name}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True),
            user: discord.PermissionOverwrite(manage_channels=True, connect=True)
        }
        
        new_channel = await guild.create_voice_channel(
            name=f"🎧 {room_name}", category=category, overwrites=overwrites, user_limit=limit
        )
        temp_voices.add(new_channel.id)
        
        try: await user.move_to(new_channel)
        except: pass
        
        await ctx.send(f"✅ Đã kéo bạn vào phòng mới: {new_channel.mention}\n*(Phòng sẽ tự xoá khi không còn ai)*")

    @commands.hybrid_command(name="quiz", description="Chơi trả lời câu hỏi trắc nghiệm")
    async def quiz(self, ctx):
        guild_id = str(ctx.guild.id)
        def query_question():
            with db_lock:
                cursor.execute(
                    "SELECT id, question, option_a, option_b, option_c, option_d, correct_option FROM quiz_questions WHERE guild_id = ? ORDER BY random() LIMIT 1",
                    (guild_id,)
                )
                return cursor.fetchone()
        row = await self.bot.loop.run_in_executor(None, query_question)
        if not row:
            return await ctx.send("❌ Máy chủ này chưa có câu hỏi nào. Admin vui lòng cấu hình câu hỏi thông qua GUI quản lý!")
        q_id, q_text, opt_a, opt_b, opt_c, opt_d, correct_opt = row
        embed = discord.Embed(
            title="❓ THỬ THÁCH TRÍ TUỆ (QUIZ)",
            description=f"**Câu hỏi:** {q_text}\n\n"
                        f"🇦 {opt_a}\n"
                        f"🇧 {opt_b}\n"
                        f"🇨 {opt_c}\n"
                        f"🇩 {opt_d}",
            color=0xF1C40F
        )
        embed.set_footer(text="Nhấn vào nút bên dưới để chọn câu trả lời (Thông tin hiển thị riêng tư cho bạn)")
        view = QuizView(q_id, correct_opt)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Utilities(bot))
