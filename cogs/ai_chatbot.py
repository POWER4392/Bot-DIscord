# Updated by POWER4392 (Backend Developer) — OpenAI (ChatGPT) & Gemini Multi-Provider Support
import discord
from discord.ext import commands
from discord import app_commands
from google import genai
from google.genai import types
import openai
import os
import time
import PIL.Image
import io
import base64
import json

from core.database import cursor, conn, db_lock

# Số lượng lượt hội thoại tối đa lưu trong DB mỗi user
MAX_HISTORY_PER_USER = 20


class AIChatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from core.shared import config
        self.provider = "openai"  # "openai" hoặc "gemini"
        self.model_name = "gpt-4o-mini"
        self.gemini_client = None
        self.openai_client = None

        # In-memory chat sessions cho Gemini: {(guild_id, user_id): genai.chats.Chat}
        self.chat_sessions: dict = {}

        # Anti-Spam Sliding Window: {user_id: [timestamps]}
        self.user_message_timestamps: dict = {}
        # Duplicate detector: {user_id: {"content": str, "count": int}}
        self.user_last_message: dict = {}

        # Spam configurations
        self.rate_limit_window = 5.0
        self.max_messages_in_window = 5
        self.max_duplicates = 3

        self.ensure_model_initialized()

    def sanitize_key(self, key: str) -> str:
        if not key:
            return ""
        k = str(key).strip()
        if (k.startswith('"') and k.endswith('"')) or (k.startswith("'") and k.endswith("'")):
            k = k[1:-1].strip()
        return k

    def ensure_model_initialized(self) -> bool:
        from core.shared import config
        raw_okey = os.getenv("OPENAI_API_KEY") or config.get("openai_api_key") or config.get("openai_key")
        raw_gkey = os.getenv("GEMINI_API_KEY") or config.get("gemini_api_key") or config.get("gemini_key")

        okey = self.sanitize_key(raw_okey)
        gkey = self.sanitize_key(raw_gkey)

        preferred = str(config.get("ai_provider", "")).strip().lower()

        if preferred == "openai" and okey:
            if self._init_openai(okey):
                return True
            if gkey and self._init_gemini(gkey):
                return True
        elif preferred == "gemini" and gkey:
            if self._init_gemini(gkey):
                return True
            if okey and self._init_openai(okey):
                return True

        if okey and self._init_openai(okey):
            return True
        elif gkey and self._init_gemini(gkey):
            return True
        return False

    def _init_openai(self, key: str) -> bool:
        try:
            from core.shared import config
            self.openai_client = openai.OpenAI(api_key=key)
            self.provider = "openai"
            self.model_name = config.get("openai_model", "gpt-4o-mini")
            print(f"[AI] OpenAI API nạp thành công với model {self.model_name}.")
            return True
        except Exception as ex:
            print(f"[AI Warning] Không nạp được OpenAI Client: {ex}")
            return False

    def _init_gemini(self, key: str) -> bool:
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-flash-latest"
        ]
        for m_name in models_to_try:
            try:
                self.model_name = m_name
                self.gemini_client = genai.Client(api_key=key)
                self.provider = "gemini"
                print(f"[AI] Gemini API nạp thành công với model {self.model_name}.")
                return True
            except Exception as ex:
                print(f"[AI Warning] Không nạp được model {m_name}: {ex}")
                continue
        return False

    # ------------------------------------------------------------------
    # Helper: Gemini Session
    # ------------------------------------------------------------------
    def _get_gemini_session(self, guild_id: int, user_id: int, system_prompt: str):
        key = (guild_id, user_id)
        if key not in self.chat_sessions:
            config_gen = types.GenerateContentConfig(system_instruction=system_prompt)
            history = self._load_history_from_db(guild_id, user_id)
            self.chat_sessions[key] = self.gemini_client.chats.create(
                model=self.model_name,
                config=config_gen,
                history=history
            )
        return self.chat_sessions[key]

    # ------------------------------------------------------------------
    # Helper: OpenAI Message History
    # ------------------------------------------------------------------
    def _get_openai_messages(self, guild_id: int, user_id: int, system_prompt: str, prompt_with_rag: str) -> list:
        messages = [{"role": "system", "content": system_prompt}]
        try:
            with db_lock:
                cursor.execute(
                    "SELECT role, content FROM ai_conversations WHERE guild_id=? AND user_id=? ORDER BY timestamp ASC LIMIT ?",
                    (str(guild_id), str(user_id), MAX_HISTORY_PER_USER * 2)
                )
                rows = cursor.fetchall()
            for role, content in rows:
                o_role = "assistant" if role in ("model", "assistant") else "user"
                messages.append({"role": o_role, "content": content})
        except Exception as e:
            print(f"[AI DB] Loi doc lich su cho OpenAI: {e}")
        
        messages.append({"role": "user", "content": prompt_with_rag})
        return messages

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
        try:
            with db_lock:
                if user_id:
                    cursor.execute(
                        "DELETE FROM ai_conversations WHERE guild_id=? AND user_id=?",
                        (str(guild_id), str(user_id))
                    )
                    self.chat_sessions.pop((guild_id, user_id), None)
                else:
                    cursor.execute(
                        "DELETE FROM ai_conversations WHERE guild_id=?",
                        (str(guild_id),)
                    )
                    keys_to_del = [k for k in self.chat_sessions if k[0] == guild_id]
                    for k in keys_to_del:
                        del self.chat_sessions[k]
                conn.commit()
        except Exception as e:
            print(f"[AI DB] Loi xoa lich su: {e}")

    # ------------------------------------------------------------------
    # Helper: RAG retrieval from server rules
    # ------------------------------------------------------------------
    def _retrieve_relevant_rules(self, query: str) -> str:
        docs_dir = "docs"
        if not os.path.exists(docs_dir):
            return ""
        try:
            all_contents = []
            for file_name in os.listdir(docs_dir):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(docs_dir, file_name)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            all_contents.append(f.read())
                    except Exception as fe:
                        print(f"[RAG] Loi khi doc file {file_name}: {fe}")

            if not all_contents:
                return ""

            content = "\n\n".join(all_contents)
            sections = content.split("\n## ")
            relevant_sections = []

            words = [w.strip(",.?/!").lower() for w in query.split() if len(w) > 2]

            for section in sections:
                full_section = ("## " + section) if not section.startswith("# ") else section
                score = 0
                section_lower = full_section.lower()
                for word in words:
                    if word in section_lower:
                        score += 1
                if score > 0:
                    relevant_sections.append((score, full_section))

            if not relevant_sections:
                return ""

            relevant_sections.sort(key=lambda x: x[0], reverse=True)
            top_sections = [sec[1] for sec in relevant_sections[:2]]

            return "\n\n".join(top_sections)
        except Exception as e:
            print(f"[RAG Error] Loi khi truy van luat le: {e}")
            return ""

    # ------------------------------------------------------------------
    # DB: Lưu thống kê token sử dụng
    # ------------------------------------------------------------------
    def _save_token_usage_to_db(self, guild_id: int, user_id: int, prompt_tokens: int, completion_tokens: int, total_tokens: int, latency_ms: int = 0):
        try:
            with db_lock:
                cursor.execute(
                    "INSERT INTO ai_token_usage (guild_id, user_id, prompt_tokens, completion_tokens, total_tokens, timestamp, latency_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(guild_id), str(user_id), prompt_tokens, completion_tokens, total_tokens, time.time(), latency_ms)
                )
                conn.commit()
        except Exception as e:
            print(f"[AI DB] Loi luu thong ke token: {e}")

    # ------------------------------------------------------------------
    # on_message
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        is_mentioned = (self.bot.user in message.mentions) if self.bot.user else False
        is_reply_to_bot = False
        if message.reference and message.reference.resolved:
            if isinstance(message.reference.resolved, discord.Message):
                if self.bot.user and message.reference.resolved.author.id == self.bot.user.id:
                    is_reply_to_bot = True

        from core.shared import config
        ai_channel_id = config.get("ai_channel_id")
        is_ai_channel = bool(ai_channel_id and str(message.channel.id) == str(ai_channel_id))

        if not (is_mentioned or is_reply_to_bot or is_ai_channel):
            return

        is_spam = await self.check_spam_protection(message)
        if is_spam:
            return

        content = message.content
        if self.bot.user:
            content = content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
        else:
            content = content.strip()

        if not content and not message.attachments:
            await message.reply("Xin chào! Bạn có thể đặt câu hỏi hoặc gửi hình ảnh cho tôi tại đây.")
            return

        if not self.ensure_model_initialized():
            await message.reply(
                "⚠️ **AI Chatbot chưa được cấu hình API Key (OpenAI / Gemini)!**\n"
                "👉 Dán API Key tại **Web Dashboard** hoặc dùng lệnh `!setkey <sk-..._hoac_key_gemini>`."
            )
            return

        await self._do_chat(message.channel, message.author, message.guild, content, reply_target=message)

    # ------------------------------------------------------------------
    # Hybrid Command: !setkey <key> / /setkey
    # ------------------------------------------------------------------
    @commands.hybrid_command(name="setkey", description="Cập nhật OpenAI (sk-...) hoặc Gemini API Key cho Bot.")
    async def setkey_cmd(self, ctx: commands.Context, key: str):
        key = self.sanitize_key(key)
        if not key or len(key) < 15:
            await ctx.send("❌ **Lỗi:** Key quá ngắn hoặc không hợp lệ. OpenAI Key bắt đầu bằng `sk-...`, Gemini Key bắt đầu bằng `AIzaSy...`.")
            return

        from core.shared import config, config_file

        is_openai_key = key.startswith("sk-")

        if is_openai_key:
            config["openai_api_key"] = key
            config["ai_provider"] = "openai"
            os.environ["OPENAI_API_KEY"] = key
        else:
            config["gemini_api_key"] = key
            config["ai_provider"] = "gemini"
            os.environ["GEMINI_API_KEY"] = key

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[SetKey Error] {e}")

        self.openai_client = None
        self.gemini_client = None
        self.chat_sessions.clear()

        if self.ensure_model_initialized():
            if self.provider == "openai":
                try:
                    test_res = await self.bot.loop.run_in_executor(
                        None,
                        lambda: self.openai_client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": "Xin chào"}]
                        )
                    )
                    if test_res and test_res.choices:
                        await ctx.send(f"✅ **Thành công!** OpenAI API Key (ChatGPT) đã được xác thực 100% (Model: `{self.model_name}`). Dùng lệnh `!ai Xin chào` để nhắn tin!")
                        return
                except Exception as test_ex:
                    await ctx.send(f"⚠️ **Đã lưu OpenAI Key nhưng API báo lỗi:** `{str(test_ex)[:150]}`")
                    return
            else:
                try:
                    test_res = await self.bot.loop.run_in_executor(
                        None,
                        lambda: self.gemini_client.models.generate_content(model=self.model_name, contents="Xin chào")
                    )
                    if test_res and test_res.text:
                        await ctx.send(f"✅ **Thành công!** Gemini API Key đã được xác thực 100% (Model: `{self.model_name}`).")
                        return
                except Exception as test_ex:
                    await ctx.send(f"⚠️ **Đã lưu Gemini Key nhưng API báo lỗi:** `{str(test_ex)[:150]}`")
                    return

            await ctx.send(f"✅ Đã nạp API Key thành công (Provider: `{self.provider}`, Model: `{self.model_name}`).")
        else:
            await ctx.send("❌ Không thể khởi tạo mô hình AI với Key này. Kiểm tra lại Key của bạn!")

    # ------------------------------------------------------------------
    # Hybrid Command: !setmodel <model>
    # ------------------------------------------------------------------
    @commands.hybrid_command(name="setmodel", description="Đổi mô hình OpenAI (gpt-4o-mini, gpt-4o, gpt-3.5-turbo) hoặc Gemini.")
    async def setmodel_cmd(self, ctx: commands.Context, model: str):
        from core.shared import config, config_file
        model = model.strip()
        if "gpt" in model.lower():
            config["openai_model"] = model
            config["ai_provider"] = "openai"
        else:
            config["ai_provider"] = "gemini"
        
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[SetModel Error] {e}")

        self.ensure_model_initialized()
        await ctx.send(f"⚙️ **Đã chuyển đổi mô hình AI:** Provider = `{self.provider}`, Model = `{self.model_name}`.")

    # ------------------------------------------------------------------
    # Hybrid Command: !ai <question>
    # ------------------------------------------------------------------
    @commands.hybrid_command(name="ai", description="Hỏi AI Chatbot câu hỏi của bạn (OpenAI / Gemini).")
    async def ai_cmd(self, ctx: commands.Context, *, question: str):
        if not self.ensure_model_initialized():
            await ctx.send("⚠️ Tính năng AI chưa được nạp Key. Dùng lệnh `!setkey <key>` để nạp Key!")
            return
        await self._do_chat(ctx.channel, ctx.author, ctx.guild, question, reply_target=ctx.message)

    # ------------------------------------------------------------------
    # Slash command: /ask
    # ------------------------------------------------------------------
    @app_commands.command(name="ask", description="Hỏi AI Chatbot (OpenAI / Gemini) hỗ trợ đính kèm hình ảnh!")
    @app_commands.describe(question="Câu hỏi của bạn hoặc lời nhắc cho hình ảnh", image="Hình ảnh đính kèm (không bắt buộc)")
    async def ask(self, interaction: discord.Interaction, question: str, image: discord.Attachment = None):
        if not self.ensure_model_initialized():
            await interaction.response.send_message(
                "⚠️ Tính năng AI Chatbot chưa được cấu hình. Vui lòng liên hệ Admin!",
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer()
        except Exception:
            pass
        await self._do_chat(
            interaction.channel,
            interaction.user,
            interaction.guild,
            question,
            interaction=interaction,
            attachment=image
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
    # Core chat logic
    # ------------------------------------------------------------------
    async def _do_chat(
        self,
        channel,
        author: discord.User,
        guild: discord.Guild,
        content: str,
        reply_target=None,
        interaction: discord.Interaction = None,
        attachment: discord.Attachment = None
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
                # Kiểm tra hình ảnh đính kèm (AI Vision)
                image_target = None
                if attachment:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        image_target = attachment
                elif reply_target and reply_target.attachments:
                    first_att = reply_target.attachments[0]
                    if first_att.content_type and first_att.content_type.startswith("image/"):
                        image_target = first_att

                # RAG: Truy vấn luật lệ liên quan
                rag_context = self._retrieve_relevant_rules(content)
                if rag_context:
                    prompt_with_rag = (
                        f"[THÔNG TIN THAM KHẢO TỪ LUẬT & HƯỚNG DẪN CỦA SERVER]\n"
                        f"{rag_context}\n\n"
                        f"[YÊU CẦU: Hãy trả lời câu hỏi sau dựa trên thông tin tham khảo trên nếu có liên quan. Trả lời ngắn gọn, tự nhiên, bằng tiếng Việt]\n"
                        f"Câu hỏi: {content}"
                    )
                else:
                    prompt_with_rag = content

                start_time = time.time()
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                reply_text = ""

                # A. XỬ LÝ VỚI OPENAI (CHATGPT)
                if self.provider == "openai" and not reply_text:
                    try:
                        if image_target:
                            image_bytes = await image_target.read()
                            base64_image = base64.b64encode(image_bytes).decode('utf-8')
                            mime_type = image_target.content_type or "image/jpeg"

                            safety_prompt_prefix = (
                                "Bạn là hệ thống kiểm duyệt hình ảnh và bản quyền an toàn thông minh của Discord Bot (AI Vision).\n"
                                "Nếu phát hiện vi phạm NSFW, máu me, tự hại hoặc logo bản quyền lớn, bắt đầu bằng: "
                                "\"CẢNH BÁO AN TOÀN: Hình ảnh chứa nội dung nhạy cảm hoặc vi phạm bản quyền và đã bị chặn bởi hệ thống AI Vision.\"\n"
                                "Nếu an toàn, trả lời bình thường bằng tiếng Việt."
                            )
                            prompt_text = f"{safety_prompt_prefix}\n{prompt_with_rag if content else 'Hãy phân tích hình ảnh này.'}"

                            self._save_message_to_db(guild_id, user_id, "user", f"[Gửi ảnh] {content or ''}")

                            messages = [
                                {"role": "system", "content": system_prompt},
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt_text},
                                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                                    ]
                                }
                            ]

                            models_to_try = [self.model_name, "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
                            last_ex = None
                            response = None
                            for m in dict.fromkeys(models_to_try):
                                try:
                                    response = await self.bot.loop.run_in_executor(
                                        None,
                                        lambda m_curr=m: self.openai_client.chat.completions.create(
                                            model=m_curr,
                                            messages=messages
                                        )
                                    )
                                    self.model_name = m
                                    break
                                except Exception as m_err:
                                    last_ex = m_err
                                    continue
                            if not response:
                                raise last_ex
                        else:
                            self._save_message_to_db(guild_id, user_id, "user", content)
                            messages = self._get_openai_messages(guild_id, user_id, system_prompt, prompt_with_rag)

                            models_to_try = [self.model_name, "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
                            last_ex = None
                            response = None
                            for m in dict.fromkeys(models_to_try):
                                try:
                                    response = await self.bot.loop.run_in_executor(
                                        None,
                                        lambda m_curr=m: self.openai_client.chat.completions.create(
                                            model=m_curr,
                                            messages=messages
                                        )
                                    )
                                    self.model_name = m
                                    break
                                except Exception as m_err:
                                    last_ex = m_err
                                    continue
                            if not response:
                                raise last_ex

                        reply_text = response.choices[0].message.content
                        if response.usage:
                            prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
                            completion_tokens = getattr(response.usage, "completion_tokens", 0)
                            total_tokens = getattr(response.usage, "total_tokens", 0)
                    except Exception as oai_err:
                        print(f"[AI Warning] Lỗi OpenAI ({oai_err}). Thử chuyển sang Gemini AI...")
                        raw_gkey = os.getenv("GEMINI_API_KEY") or config.get("gemini_api_key") or config.get("gemini_key")
                        gkey = self.sanitize_key(raw_gkey)
                        if gkey and self._init_gemini(gkey):
                            print(f"[AI Fallback] Chuyển đổi thành công sang Gemini model {self.model_name}.")
                        else:
                            raise oai_err

                # B. XỬ LÝ VỚI GOOGLE GEMINI (Nếu Gemini là ưu tiên HOẶC nếu OpenAI bị lỗi)
                if self.provider == "gemini" and not reply_text:
                    try:
                        models_to_try = [self.model_name, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-flash-latest"]
                        last_g_ex = None
                        response = None

                        if image_target:
                            image_bytes = await image_target.read()
                            image_pil = PIL.Image.open(io.BytesIO(image_bytes))

                            safety_prompt_prefix = (
                                "Bạn là hệ thống kiểm duyệt hình ảnh và bản quyền an toàn thông minh của Discord Bot (AI Vision).\n"
                                "Nếu vi phạm, trả lời: \"CẢNH BÁO AN TOÀN: Hình ảnh chứa nội dung nhạy cảm hoặc vi phạm bản quyền và đã bị chặn bởi hệ thống AI Vision.\"\n"
                                "Nếu an toàn, trả lời bình thường bằng tiếng Việt."
                            )
                            prompt = f"{safety_prompt_prefix}\n{prompt_with_rag if content else 'Hãy phân tích hình ảnh này.'}"

                            self._save_message_to_db(guild_id, user_id, "user", f"[Gửi ảnh] {content or ''}")

                            for m in dict.fromkeys(models_to_try):
                                try:
                                    response = await self.bot.loop.run_in_executor(
                                        None,
                                        lambda m_curr=m: self.gemini_client.models.generate_content(model=m_curr, contents=[prompt, image_pil])
                                    )
                                    self.model_name = m
                                    break
                                except Exception as m_err:
                                    last_g_ex = m_err
                                    continue
                            if response and hasattr(response, "text"):
                                reply_text = response.text
                            else:
                                raise last_g_ex
                        else:
                            self._save_message_to_db(guild_id, user_id, "user", content)
                            try:
                                session = self._get_gemini_session(guild_id, user_id, system_prompt)
                                response = await self.bot.loop.run_in_executor(
                                    None,
                                    lambda: session.send_message(prompt_with_rag)
                                )
                                reply_text = response.text
                            except Exception as ex:
                                print(f"[AI Session Warning] Lỗi Gemini session chat ({ex}), thử generate_content...")
                                self.chat_sessions.pop((guild_id, user_id), None)
                                for m in dict.fromkeys(models_to_try):
                                    try:
                                        response = await self.bot.loop.run_in_executor(
                                            None,
                                            lambda m_curr=m: self.gemini_client.models.generate_content(
                                                model=m_curr,
                                                contents=f"{system_prompt}\n\n{prompt_with_rag}"
                                            )
                                        )
                                        self.model_name = m
                                        break
                                    except Exception as m_err:
                                        last_g_ex = m_err
                                        continue
                                if response and hasattr(response, "text"):
                                    reply_text = response.text
                                else:
                                    raise (last_g_ex or ex)

                        if hasattr(response, "usage_metadata") and response.usage_metadata:
                            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
                            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
                            total_tokens = getattr(response.usage_metadata, "total_token_count", 0)
                    except Exception as gem_err:
                        print(f"[AI Warning] Lỗi Gemini ({gem_err}). Thử chuyển sang OpenAI...")
                        raw_okey = os.getenv("OPENAI_API_KEY") or config.get("openai_api_key") or config.get("openai_key")
                        okey = self.sanitize_key(raw_okey)
                        if okey and self._init_openai(okey):
                            print(f"[AI Fallback] Chuyển đổi thành công sang OpenAI model {self.model_name}.")
                        else:
                            raise gem_err

                # C. FALLBACK SANG OPENAI (Nếu Gemini ban đầu bị lỗi)
                if self.provider == "openai" and not reply_text:
                    if image_target:
                        image_bytes = await image_target.read()
                        base64_image = base64.b64encode(image_bytes).decode('utf-8')
                        mime_type = image_target.content_type or "image/jpeg"

                        safety_prompt_prefix = (
                            "Bạn là hệ thống kiểm duyệt hình ảnh và bản quyền an toàn thông minh của Discord Bot (AI Vision).\n"
                            "Nếu phát hiện vi phạm NSFW, máu me, tự hại hoặc logo bản quyền lớn, bắt đầu bằng: "
                            "\"CẢNH BÁO AN TOÀN: Hình ảnh chứa nội dung nhạy cảm hoặc vi phạm bản quyền và đã bị chặn bởi hệ thống AI Vision.\"\n"
                            "Nếu an toàn, trả lời bình thường bằng tiếng Việt."
                        )
                        prompt_text = f"{safety_prompt_prefix}\n{prompt_with_rag if content else 'Hãy phân tích hình ảnh này.'}"

                        messages = [
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_text},
                                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                                ]
                            }
                        ]

                        models_to_try = [self.model_name, "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
                        last_ex = None
                        response = None
                        for m in dict.fromkeys(models_to_try):
                            try:
                                response = await self.bot.loop.run_in_executor(
                                    None,
                                    lambda m_curr=m: self.openai_client.chat.completions.create(
                                        model=m_curr,
                                        messages=messages
                                    )
                                )
                                self.model_name = m
                                break
                            except Exception as m_err:
                                last_ex = m_err
                                continue
                        if response and hasattr(response, "choices"):
                            reply_text = response.choices[0].message.content
                        else:
                            raise last_ex
                    else:
                        messages = self._get_openai_messages(guild_id, user_id, system_prompt, prompt_with_rag)
                        models_to_try = [self.model_name, "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
                        last_ex = None
                        response = None
                        for m in dict.fromkeys(models_to_try):
                            try:
                                response = await self.bot.loop.run_in_executor(
                                    None,
                                    lambda m_curr=m: self.openai_client.chat.completions.create(
                                        model=m_curr,
                                        messages=messages
                                    )
                                )
                                self.model_name = m
                                break
                            except Exception as m_err:
                                last_ex = m_err
                                continue
                        if response and hasattr(response, "choices"):
                            reply_text = response.choices[0].message.content
                        else:
                            raise last_ex

                    if response and getattr(response, "usage", None):
                        prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
                        completion_tokens = getattr(response.usage, "completion_tokens", 0)
                        total_tokens = getattr(response.usage, "total_tokens", 0)

                latency_ms = int((time.time() - start_time) * 1000)

                self._save_token_usage_to_db(guild_id, user_id, prompt_tokens, completion_tokens, total_tokens, latency_ms)
                self._save_message_to_db(guild_id, user_id, "assistant" if self.provider == "openai" else "model", reply_text)

                if len(reply_text) > 1990:
                    reply_text = reply_text[:1990] + "..."

                if interaction:
                    await interaction.followup.send(f"🤖 **{author.display_name}:** {content or '[Hình ảnh]'}\n\n{reply_text}")
                elif reply_target:
                    await reply_target.reply(reply_text)
                else:
                    await channel.send(reply_text)

            except Exception as e:
                err_str = str(e)
                print(f"[AI Error] Lỗi khi gọi {self.provider} API: {err_str}")
                err_msg = f"❌ **Lỗi kết nối {self.provider.upper()} AI:** `{err_str[:200]}`"

                if interaction:
                    await interaction.followup.send(err_msg)
                elif reply_target:
                    await reply_target.reply(err_msg)
                else:
                    await channel.send(err_msg)

    # ------------------------------------------------------------------
    # Anti-Spam Protection
    # ------------------------------------------------------------------
    async def check_spam_protection(self, message: discord.Message) -> bool:
        user_id = message.author.id
        current_time = time.time()

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
