# Updated by POWER4392 (Backend Developer) — Issue #32 Tuan 4.1
import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
import os
import time

from core.database import cursor, conn, db_lock

# Số lượng lượt hội thoại tối đa lưu trong DB mỗi user
MAX_HISTORY_PER_USER = 20


class AIChatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-1.5-flash"
        self.model = None

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                print(f"[AI] Gemini API da duoc cau hinh thanh cong. (Model: {self.model_name})")
            except Exception as e:
                print(f"[AI Error] Loi khi cau hinh Gemini: {e}")

        # In-memory chat sessions: {(guild_id, user_id): genai.ChatSession}
        self.chat_sessions: dict = {}

        # Anti-Spam Sliding Window: {user_id: [timestamps]}
        self.user_message_timestamps: dict = {}
        # Duplicate detector: {user_id: {"content": str, "count": int}}
        self.user_last_message: dict = {}

        # Spam configurations
        self.rate_limit_window = 5.0
        self.max_messages_in_window = 5
        self.max_duplicates = 3

    # ------------------------------------------------------------------
    # Helper: lấy hoặc tạo chat session cho (guild_id, user_id)
    # ------------------------------------------------------------------
    def _get_session(self, guild_id: int, user_id: int, system_prompt: str) -> "genai.ChatSession":
        key = (guild_id, user_id)
        if key not in self.chat_sessions:
            dynamic_model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt
            )
            # Nạp lịch sử từ DB
            history = self._load_history_from_db(guild_id, user_id)
            self.chat_sessions[key] = dynamic_model.start_chat(history=history)
        return self.chat_sessions[key]

    # ------------------------------------------------------------------
    # DB: Lưu lịch sử hội thoại
    # ------------------------------------------------------------------
    def _save_message_to_db(self, guild_id: int, user_id: int, role: str, content: str):
        try:
            with db_lock:
                cursor.execute(
                    "INSERT INTO ai_conversations (guild_id, user_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (str(guild_id), str(user_id), role, content, time.time())
                )
                conn.commit()
                # Giữ chỉ MAX_HISTORY_PER_USER*2 bản ghi mới nhất
                # SQLite không hỗ trợ LIMIT trong subquery của DELETE → dùng 2 bước
                cursor.execute(
                    "SELECT id FROM ai_conversations WHERE guild_id=? AND user_id=? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (str(guild_id), str(user_id), MAX_HISTORY_PER_USER * 2)
                )
                keep_ids = [row[0] for row in cursor.fetchall()]
                if keep_ids:
                    placeholders = ",".join("?" * len(keep_ids))
                    cursor.execute(
                        f"DELETE FROM ai_conversations WHERE guild_id=? AND user_id=? "
                        f"AND id NOT IN ({placeholders})",
                        [str(guild_id), str(user_id)] + keep_ids
                    )
                    conn.commit()
        except Exception as e:
            print(f"[AI DB] Loi luu lich su: {e}")

    def _load_history_from_db(self, guild_id: int, user_id: int) -> list:
        """Trả về history ở định dạng genai Content list."""
        try:
            with db_lock:
                cursor.execute(
                    "SELECT role, content FROM ai_conversations WHERE guild_id=? AND user_id=? ORDER BY timestamp ASC LIMIT ?",
                    (str(guild_id), str(user_id), MAX_HISTORY_PER_USER * 2)
                )
                rows = cursor.fetchall()
            history = []
            for role, content in rows:
                history.append({"role": role, "parts": [content]})
            return history
        except Exception as e:
            print(f"[AI DB] Loi doc lich su: {e}")
            return []

    def _clear_history_in_db(self, guild_id: int, user_id: int = None):
        """Xóa lịch sử theo guild hoặc user cụ thể."""
        try:
            with db_lock:
                if user_id:
                    cursor.execute(
                        "DELETE FROM ai_conversations WHERE guild_id=? AND user_id=?",
                        (str(guild_id), str(user_id))
                    )
                    # Xóa session in-memory
                    self.chat_sessions.pop((guild_id, user_id), None)
                else:
                    cursor.execute(
                        "DELETE FROM ai_conversations WHERE guild_id=?",
                        (str(guild_id),)
                    )
                    # Xóa tất cả session in-memory của guild
                    keys_to_del = [k for k in self.chat_sessions if k[0] == guild_id]
                    for k in keys_to_del:
                        del self.chat_sessions[k]
                conn.commit()
        except Exception as e:
            print(f"[AI DB] Loi xoa lich su: {e}")

    # ------------------------------------------------------------------
    # on_message: phản hồi trong AI channel hoặc khi được mention
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Anti-Spam check
        is_spam = await self.check_spam_protection(message)
        if is_spam:
            return

        is_mentioned = self.bot.user in message.mentions
        from core.shared import config
        ai_channel_id = config.get("ai_channel_id")
        is_ai_channel = ai_channel_id and str(message.channel.id) == str(ai_channel_id)

        if not (is_mentioned or is_ai_channel):
            return

        content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
        if not content:
            await message.reply("Xin chào! Bạn có thể đặt câu hỏi cho tôi tại đây.")
            return

        if not self.model:
            await message.reply(
                "⚠️ Tính năng AI Chatbot chưa được cấu hình API Key (GEMINI_API_KEY). Vui lòng liên hệ Admin!"
            )
            return

        await self._do_chat(message.channel, message.author, message.guild, content, reply_target=message)

    # ------------------------------------------------------------------
    # Slash command: /ask
    # ------------------------------------------------------------------
    @app_commands.command(name="ask", description="Hỏi AI Chatbot bất kỳ điều gì!")
    @app_commands.describe(question="Câu hỏi của bạn")
    async def ask(self, interaction: discord.Interaction, question: str):
        if not self.model:
            await interaction.response.send_message(
                "⚠️ Tính năng AI Chatbot chưa được cấu hình. Vui lòng liên hệ Admin!",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        await self._do_chat(
            interaction.channel,
            interaction.user,
            interaction.guild,
            question,
            interaction=interaction
        )

    # ------------------------------------------------------------------
    # Slash command: /clear_history
    # ------------------------------------------------------------------
    @app_commands.command(name="clear_history", description="Xóa lịch sử hội thoại AI của bạn với Bot.")
    async def clear_history(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("Lệnh này chỉ dùng được trong server.", ephemeral=True)
            return

        self._clear_history_in_db(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(
            "🗑️ Đã xóa toàn bộ lịch sử hội thoại AI của bạn. Cuộc trò chuyện mới bắt đầu!",
            ephemeral=True
        )

    # ------------------------------------------------------------------
    # Core chat logic (dùng chung cho on_message và /ask)
    # ------------------------------------------------------------------
    async def _do_chat(
        self,
        channel,
        author: discord.User,
        guild: discord.Guild,
        content: str,
        reply_target=None,
        interaction: discord.Interaction = None
    ):
        from core.shared import config
        system_prompt = config.get(
            "ai_system_prompt",
            "Bạn là một trợ lý ảo Discord thân thiện, nhiệt tình, hỗ trợ thành viên server."
        )

        guild_id = guild.id if guild else 0
        user_id = author.id

        async with channel.typing():
            try:
                session = self._get_session(guild_id, user_id, system_prompt)

                # Lưu tin nhắn user vào DB
                self._save_message_to_db(guild_id, user_id, "user", content)

                # Gọi Gemini (bất đồng bộ qua executor để không block event loop)
                response = await self.bot.loop.run_in_executor(
                    None,
                    lambda: session.send_message(content)
                )
                reply_text = response.text

                # Lưu phản hồi của model vào DB
                self._save_message_to_db(guild_id, user_id, "model", reply_text)

                # Giới hạn 2000 ký tự (giới hạn Discord)
                if len(reply_text) > 1990:
                    reply_text = reply_text[:1990] + "..."

                if interaction:
                    await interaction.followup.send(f"🤖 **{author.display_name}:** {content}\n\n{reply_text}")
                elif reply_target:
                    await reply_target.reply(reply_text)
                else:
                    await channel.send(reply_text)

            except Exception as e:
                print(f"[AI Error] Loi khi goi Gemini API: {e}")
                err_msg = "❌ Đã xảy ra lỗi khi kết nối với AI. Vui lòng thử lại sau."
                if interaction:
                    await interaction.followup.send(err_msg)
                elif reply_target:
                    await reply_target.reply(err_msg)
                else:
                    await channel.send(err_msg)

    # ------------------------------------------------------------------
    # Anti-Spam: Sliding Window + Duplicate detector
    # ------------------------------------------------------------------
    async def check_spam_protection(self, message: discord.Message) -> bool:
        user_id = message.author.id
        current_time = time.time()

        # A. Sliding Window Rate Limiter
        if user_id not in self.user_message_timestamps:
            self.user_message_timestamps[user_id] = []

        timestamps = self.user_message_timestamps[user_id]
        timestamps = [ts for ts in timestamps if current_time - ts < self.rate_limit_window]
        timestamps.append(current_time)
        self.user_message_timestamps[user_id] = timestamps

        if len(timestamps) > self.max_messages_in_window:
            try:
                await message.channel.send(
                    f"⚠️ **Cảnh báo Spam:** {message.author.mention}, bạn đang nhắn tin quá nhanh! Vui lòng làm chậm lại."
                )
            except Exception:
                pass
            return True

        # B. Duplicate Content Detection
        content = message.content.strip().lower()
        if content:
            last_msg = self.user_last_message.get(user_id, {"content": "", "count": 0})
            if last_msg["content"] == content:
                last_msg["count"] += 1
            else:
                last_msg = {"content": content, "count": 1}

            self.user_last_message[user_id] = last_msg

            if last_msg["count"] >= self.max_duplicates:
                try:
                    await message.channel.send(
                        f"⚠️ **Cảnh báo Spam:** {message.author.mention}, vui lòng không gửi lặp lại cùng một nội dung."
                    )
                except Exception:
                    pass
                return True

        return False


async def setup(bot):
    await bot.add_cog(AIChatbot(bot))
