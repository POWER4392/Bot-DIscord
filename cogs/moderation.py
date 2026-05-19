import discord
from discord.ext import commands
import os
import json
import datetime
import time
import asyncio
import re
from core.shared import config, anti_nuke_tracker, spam_tracker, SCAM_REGEX_GLOBAL
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

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_cache = {}
        self.bot.loop.create_task(self.load_blacklist_cache())

    async def load_blacklist_cache(self):
        await self.bot.wait_until_ready()
        def fetch_all():
            with db_lock:
                cursor.execute("SELECT guild_id, word FROM blacklists")
                return cursor.fetchall()
        try:
            rows = await self.bot.loop.run_in_executor(None, fetch_all)
            for guild_id, word in rows:
                g_id = str(guild_id)
                if g_id not in self.blacklist_cache:
                    self.blacklist_cache[g_id] = []
                self.blacklist_cache[g_id].append(word.strip().lower())
            print(f"[AutoMod] Đã nạp thành công blacklist cache cho {len(self.blacklist_cache)} server.")
        except Exception as e:
            print(f"[AutoMod] Lỗi nạp blacklist cache: {e}")

    async def check_anti_nuke(self, guild, action_type):
        now = datetime.datetime.now().timestamp()
        bot_member = guild.me
        if not bot_member.guild_permissions.view_audit_log: return
        try:
            action_mapping = {"channel_delete": discord.AuditLogAction.channel_delete, "role_delete": discord.AuditLogAction.role_delete}
            async for entry in guild.audit_logs(action=action_mapping[action_type], limit=1):
                user = entry.user
                if user.bot: return
                
                guild_id = str(guild.id)
                if guild_id not in anti_nuke_tracker: anti_nuke_tracker[guild_id] = {}
                if user.id not in anti_nuke_tracker[guild_id]: anti_nuke_tracker[guild_id][user.id] = []
                
                anti_nuke_tracker[guild_id][user.id] = [t for t in anti_nuke_tracker[guild_id][user.id] if now - t <= 30]
                anti_nuke_tracker[guild_id][user.id].append(now)
                
                if len(anti_nuke_tracker[guild_id][user.id]) >= 3:
                    server_cfg = config.get("servers", {}).get(guild_id, config)
                    log_channel_id = server_cfg.get("log_channel_id") or server_cfg.get("automod_channel_id")
                    if log_channel_id:
                        log_channel = self.bot.get_channel(int(log_channel_id))
                        if log_channel:
                            embed = discord.Embed(title="🚨 ANTI-NUKE TRIGGERED 🚨", description=f"**{user.name}** đã xóa liên tục kênh/vai trò ({len(anti_nuke_tracker[guild_id][user.id])} lần/30s)!\nHành vi phá hoại đang diễn ra!", color=0x990000)
                            try: await log_channel.send(embed=embed)
                            except: pass
                    
                    try:
                        for r in user.roles:
                            if r.name != "@everyone" and bot_member.top_role > r:
                                await user.remove_roles(r)
                    except: pass
                    anti_nuke_tracker[guild_id][user.id].clear()
                break
        except: pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, r): 
        await self.check_anti_nuke(r.guild, "role_delete")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, c): 
        await self.check_anti_nuke(c.guild, "channel_delete")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        guild_id = str(message.guild.id) if message.guild else None
        if not guild_id: return
        server_cfg = config.get("servers", {}).get(guild_id, config)
        log_channel_id = server_cfg.get("log_channel_id") or server_cfg.get("automod_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                content_display = message.content or "*(Không có nội dung văn bản — có thể là ảnh/file)*"
                embed = discord.Embed(title="🗑️ Tin nhắn bị Xóa", description=content_display[:2000], color=0xFF0000)
                embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                embed.set_footer(text=f"Kênh: {message.channel.name} | {datetime.datetime.now().strftime('%H:%M:%S')}")
                if message.attachments:
                    att_list = "\n".join(f"📎 {a.filename}" for a in message.attachments)
                    embed.add_field(name="File đính kèm", value=att_list[:1024], inline=False)
                try: await log_channel.send(embed=embed)
                except: pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content: return
        guild_id = str(before.guild.id) if before.guild else None
        if not guild_id: return
        server_cfg = config.get("servers", {}).get(guild_id, config)
        log_channel_id = server_cfg.get("log_channel_id") or server_cfg.get("automod_channel_id")
        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                embed = discord.Embed(title="📝 Tin nhắn bị Sửa", color=0xFFA500)
                embed.set_author(name=before.author.name, icon_url=before.author.display_avatar.url)
                b_content = before.content or "*(Trống)*"
                a_content = after.content or "*(Trống)*"
                embed.add_field(name="Trước", value=b_content[:1024], inline=False)
                embed.add_field(name="Sau", value=a_content[:1024], inline=False)
                embed.set_footer(text=f"Kênh: {before.channel.name} | {datetime.datetime.now().strftime('%H:%M:%S')}")
                embed.description = f"[Nhảy đến tin nhắn]({after.jump_url})"
                try: await log_channel.send(embed=embed)
                except: pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        guild_id = str(message.guild.id) if message.guild else None
        if not guild_id: return
        
        server_cfg = config.get("servers", {}).get(guild_id, config)
        is_mod_or_admin = message.author.guild_permissions.administrator
        if not is_mod_or_admin:
            mod_role_ids = server_cfg.get("mod_role_ids", [])
            old_mod_role_id = server_cfg.get("mod_role_id")
            if old_mod_role_id and old_mod_role_id not in mod_role_ids: mod_role_ids.append(old_mod_role_id)
            user_role_ids = [str(r.id) for r in message.author.roles]
            if any(str(m_id) in user_role_ids for m_id in mod_role_ids):
                is_mod_or_admin = True
                
        if not is_mod_or_admin:
            msg_text = message.content or ""
            if msg_text and SCAM_REGEX_GLOBAL.search(msg_text):
                try: await message.delete()
                except: pass
                try:
                    await message.author.timeout(datetime.timedelta(hours=1), reason="Phát tán Phishing/Scam Link")
                    await message.channel.send(f"🚨 Đã bắt giữ và Timeout {message.author.mention} 1 giờ vì phát tán Link độc hại/Phishing!")
                except: pass
                log_chan = self.bot.get_channel(int(server_cfg.get("log_channel_id") or 0)) or self.bot.get_channel(int(server_cfg.get("automod_channel_id") or 0))
                if log_chan:
                    try: await log_chan.send(embed=discord.Embed(title="🚧 SYSTEM: Phishing Detected", description=f"Kẻ phát tán: {message.author.mention}\nNội dung: {message.content}", color=0xFF0000))
                    except: pass
                return
                
            user_id = str(message.author.id)
            if guild_id not in spam_tracker: spam_tracker[guild_id] = {}
            if user_id not in spam_tracker[guild_id]: spam_tracker[guild_id][user_id] = []
            
            now_ts = time.time()
            spam_tracker[guild_id][user_id] = [t for t in spam_tracker[guild_id][user_id] if now_ts - t <= 3.5]
            spam_tracker[guild_id][user_id].append(now_ts)
            
            if len(spam_tracker[guild_id][user_id]) >= 5:
                try: await message.delete()
                except: pass
                try:
                    await message.author.timeout(datetime.timedelta(minutes=5), reason="Spam chat")
                    await message.channel.send(f"🔇 {message.author.mention} đã bị Timeout 5 phút vì chat quá trớn (Spam)!")
                except: pass
                log_chan = self.bot.get_channel(int(server_cfg.get("log_channel_id") or 0)) or self.bot.get_channel(int(server_cfg.get("automod_channel_id") or 0))
                if log_chan:
                    try: await log_chan.send(embed=discord.Embed(title="🚧 SYSTEM: Anti-Spam Triggered", description=f"Tội phạm: {message.author.mention} nháy >5 tin / 3.5s", color=0xFFA500))
                    except: pass
                spam_tracker[guild_id][user_id].clear()
                return

        banned_words = self.blacklist_cache.get(guild_id, [])
            
        if banned_words and not is_mod_or_admin:
            banned_words = [w.strip().lower() for w in banned_words if w.strip()]
            msg_lower = (message.content or "").lower()
            trigger_word = None
            for word in banned_words:
                if word in msg_lower:
                    trigger_word = word
                    break
            
            if trigger_word:
                try: await message.delete()
                except: pass
                
                mute_minutes = server_cfg.get("automod_mute_minutes", 5)
                try:
                    duration = datetime.timedelta(minutes=int(mute_minutes))
                    await message.author.timeout(duration, reason=f"AutoMod: Sử dụng từ cấm ({trigger_word})")
                except: pass
                
                log_channel_id = server_cfg.get("automod_channel_id")
                embed = discord.Embed(color=0x2B2D31, description=message.content)
                embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
                embed.set_footer(text=f"Từ khóa: {trigger_word} • Quy tắc: Chặn các từ bị cấm • Lý do: Gửi tin nhắn chứa từ cấm")
                log_msg = f"**AutoMod** ☑️ `[CHÍNH THỨC]` đã cách ly một thành viên do sử dụng ngôn từ không phù hợp."
                
                if log_channel_id:
                    log_channel = self.bot.get_channel(int(log_channel_id))
                    if log_channel:
                        try: await log_channel.send(content=log_msg, embed=embed)
                        except: pass
                else:
                    try: await message.channel.send(content=log_msg, embed=embed)
                    except: pass

    @commands.hybrid_command(name=config.get("cmd_warn", "warn") or "warn", description="Cảnh cáo thành viên. 3 lần = Mute 10p, 5 lần = Kick.")
    @is_mod()
    async def warn_user(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        guild_id, user_id = str(ctx.guild.id), str(member.id)
        with db_lock:
            cursor.execute("SELECT warn_count FROM warnings WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            row = cursor.fetchone()
            warn_count = row[0] + 1 if row else 1
            cursor.execute("INSERT OR REPLACE INTO warnings (guild_id, user_id, warn_count) VALUES (?, ?, ?)", (guild_id, user_id, warn_count))
            conn.commit()
        
        await ctx.send(f"⚠️ **{member.name}** đã bị cảnh cáo lần {warn_count}! Lý do: {reason}")
        
        if warn_count == 3:
            try:
                duration = datetime.timedelta(minutes=10)
                await member.timeout(duration, reason="Phạt cảnh cáo 3 lần")
                await ctx.send(f"🔇 **{member.name}** đã bị tự động Timeout 10 phút do nhận 3 cảnh cáo!")
            except: pass
        elif warn_count >= 5:
            try:
                await member.kick(reason="Phạt cảnh cáo 5 lần")
                await ctx.send(f"🔨 **{member.name}** đã bị tự động Kick khỏi server do nhận 5 cảnh cáo!")
                with db_lock:
                    cursor.execute("DELETE FROM warnings WHERE guild_id=? AND user_id=?", (guild_id, user_id))
                    conn.commit()
            except: pass

    @commands.hybrid_command(name="unwarn", description="Xoá toàn bộ cảnh cáo của một thành viên.")
    @is_mod()
    async def unwarn_user(self, ctx, member: discord.Member):
        guild_id, user_id = str(ctx.guild.id), str(member.id)
        with db_lock:
            cursor.execute("DELETE FROM warnings WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            conn.commit()
        await ctx.send(f"✅ Đã xoá sạch toàn bộ cảnh cáo của **{member.name}**. Tờ giấy trắng tinh!") 

    @commands.hybrid_command(name="warns", description="Xem số lượng cảnh cáo của một thành viên.")
    @is_mod()
    async def warns_user(self, ctx, member: discord.Member):
        guild_id, user_id = str(ctx.guild.id), str(member.id)
        with db_lock:
            cursor.execute("SELECT warn_count FROM warnings WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            row = cursor.fetchone()
        count = row[0] if row else 0
        if count == 0:
            status_msg = "✅ Thành viên này chưa có cảnh cáo nào."
        elif count < 3:
            status_msg = f"⚠️ Còn {3 - count} lần nữa sẽ bị Timeout 10 phút."
        elif count < 5:
            status_msg = f"🔇 Còn {5 - count} lần nữa sẽ bị Kick khỏi server!"
        else:
            status_msg = "🔨 Đã đủ 5 cảnh cáo — sẽ bị Kick ngay lần vi phạm tiếp theo!"
        embed = discord.Embed(
            title=f"⚠️ Hồ Sơ Vi Phạm — {member.display_name}",
            description=f"Số cảnh cáo: **{count}/5**\n{status_msg}",
            color=0xFF0000 if count >= 5 else (0xFFA500 if count >= 3 else 0xF1C40F)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name=config.get("cmd_timed_role", "timed_role") or "timed_role", description="Cấp vai trò cho người dùng trong thời gian nhất định (Giờ).")
    @is_mod()
    async def add_timed_role(self, ctx, member: discord.Member, role: discord.Role, hours: float):
        try:
            await member.add_roles(role)
            expires_at = datetime.datetime.now().timestamp() + (hours * 3600)
            with db_lock:
                cursor.execute("INSERT OR REPLACE INTO timed_roles (guild_id, user_id, role_id, expires_at) VALUES (?, ?, ?, ?)", 
                               (str(ctx.guild.id), str(member.id), str(role.id), expires_at))
                conn.commit()
            await ctx.send(f"⏳ Đã cấp quyền **{role.name}** cho **{member.name}** trong {hours} giờ.")
        except Exception as e:
            await ctx.send(f"❌ Thuật toán thất bại. Bot không có quyền cấp Role này: {e}")

    @commands.hybrid_command(name=config.get("cmd_kick", "kick") or "kick")
    @is_mod()
    async def kick_user(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        try:
            await member.kick(reason=reason)
            await ctx.send(f"🔨 Đã sút **{member.name}** rời khỏi nhóm! Lý do: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")

    @commands.hybrid_command(name=config.get("cmd_mute", "mute") or "mute")
    @is_mod()
    async def mute_user(self, ctx, member: discord.Member, minutes: int, *, reason: str = "Không có lý do"):
        try:
            duration = datetime.timedelta(minutes=minutes)
            await member.timeout(duration, reason=reason)
            await ctx.send(f"🔇 Đã cấm ngôn **{member.name}** trong {minutes} phút. Lý do: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")

    @commands.hybrid_command(name=config.get("cmd_ban", "ban") or "ban")
    @is_mod()
    async def ban_user(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        try:
            await member.ban(reason=reason)
            await ctx.send(f"⛔ Đã tử hình **{member.name}** vĩnh viễn khỏi server! Lời cuối: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")

    @commands.hybrid_command(name="unban", description="Gỡ lệnh cấm cho người dùng theo User ID.")
    @is_mod()
    async def unban_user(self, ctx, user_id: str, *, reason: str = "Không có lý do"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f"✅ Đã ân xá **{user.name}** khỏi danh sách đen! Lý do: {reason}")
        except discord.NotFound:
            await ctx.send(f"❌ Không tìm thấy User ID `{user_id}` trong danh sách bị ban.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")

    @commands.hybrid_command(name=config.get("cmd_clear", "clear") or "clear")
    @is_mod()
    async def clear_messages(self, ctx, amount: int = 5):
        try:
            await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"🧹 Đã quét dọn {amount} cọng rác tin nhắn!")
            await asyncio.sleep(4)
            await msg.delete()
        except Exception as e:
            await ctx.send(f"❌ Lỗi quét rác: {e}")

    @commands.hybrid_command(name=config.get("cmd_addword", "addword") or "addword")
    @is_mod()
    async def block_addword(self, ctx, *, word: str):
        guild_id = str(ctx.guild.id)
        word = word.strip().lower()
        with db_lock:
            cursor.execute("SELECT 1 FROM blacklists WHERE guild_id=? AND word=?", (guild_id, word))
            if cursor.fetchone():
                return await ctx.send(f"⚠️ Từ `{word}` đã tồn tại trong danh sách cấm.")
            cursor.execute("INSERT OR IGNORE INTO blacklists (guild_id, word) VALUES (?, ?)", (guild_id, word))
            conn.commit()
            
        if guild_id not in self.blacklist_cache:
            self.blacklist_cache[guild_id] = []
        if word not in self.blacklist_cache[guild_id]:
            self.blacklist_cache[guild_id].append(word)
            
        await ctx.send(f"✅ Đã thêm `{word}` vào danh sách từ cấm của Server.")

    @commands.hybrid_command(name=config.get("cmd_delword", "delword") or "delword")
    @is_mod()
    async def block_delword(self, ctx, *, word: str):
        guild_id = str(ctx.guild.id)
        word = word.strip().lower()
        with db_lock:
            cursor.execute("SELECT 1 FROM blacklists WHERE guild_id=? AND word=?", (guild_id, word))
            if not cursor.fetchone():
                return await ctx.send(f"⚠️ Từ `{word}` không nằm trong danh sách cấm.")
            cursor.execute("DELETE FROM blacklists WHERE guild_id=? AND word=?", (guild_id, word))
            conn.commit()
            
        if guild_id in self.blacklist_cache and word in self.blacklist_cache[guild_id]:
            self.blacklist_cache[guild_id].remove(word)
            
        await ctx.send(f"🗑️ Đã xoá `{word}` khỏi danh sách từ cấm của Server.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
