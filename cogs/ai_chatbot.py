# Updated by duynguyen1012 (AI/ML & Security Engineer)
import discord
from discord.ext import commands
import google.generativeai as genai
import os
import time

class AIChatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("[AI] Gemini API da duoc cau hinh thanh cong.")
            except Exception as e:
                print(f"[AI Error] Loi khi cau hinh Gemini: {e}")
                
        # Data structures for Anti-Spam model (Sliding Window & Duplicate detector)
        self.user_message_timestamps = {}  # {user_id: [timestamps]}
        self.user_last_message = {}        # {user_id: {"content": str, "count": int}}
        
        # Spam configurations
        self.rate_limit_window = 5.0       # Window size in seconds
        self.max_messages_in_window = 5    # Max messages allowed in window
        self.max_duplicates = 3            # Max duplicate messages allowed

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # 1. Anti-Spam Filtering Logic (Sliding Window & Duplicate check)
        is_spam = await self.check_spam_protection(message)
        if is_spam:
            return

        # 2. AI Chatbot logic
        is_mentioned = self.bot.user in message.mentions
        from core.shared import config
        ai_channel_id = config.get("ai_channel_id")
        is_ai_channel = ai_channel_id and str(message.channel.id) == str(ai_channel_id)

        if is_mentioned or is_ai_channel:
            content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not content:
                await message.reply("Xin chào! Bạn có thể đặt câu hỏi cho tôi bằng cách nhắn tin trực tiếp tại đây.")
                return

            if not self.model:
                await message.reply("⚠️ Tính năng AI Chatbot chưa được cấu hình API Key (GEMINI_API_KEY). Vui lòng liên hệ Admin!")
                return

            async with message.channel.typing():
                try:
                    loop = self.bot.loop
                    system_prompt = config.get("ai_system_prompt", "Bạn là một trợ lý ảo Discord thân thiện.")
                    dynamic_model = genai.GenerativeModel('gemini-pro', system_instruction=system_prompt)
                    response = await loop.run_in_executor(
                        None, 
                        lambda: dynamic_model.generate_content(content)
                    )
                    reply_text = response.text
                    if len(reply_text) > 2000:
                        reply_text = reply_text[:1990] + "..."
                    await message.reply(reply_text)
                except Exception as e:
                    print(f"[AI Error] Loi khi goi Gemini API: {e}")
                    await message.reply("❌ Đã xảy ra lỗi khi kết nối với AI. Vui lòng thử lại sau.")

    async def check_spam_protection(self, message):
        user_id = message.author.id
        current_time = time.time()
        
        # A. Sliding Window Rate Limiter
        if user_id not in self.user_message_timestamps:
            self.user_message_timestamps[user_id] = []
        
        timestamps = self.user_message_timestamps[user_id]
        # Keep only timestamps within the sliding window
        timestamps = [ts for ts in timestamps if current_time - ts < self.rate_limit_window]
        timestamps.append(current_time)
        self.user_message_timestamps[user_id] = timestamps
        
        if len(timestamps) > self.max_messages_in_window:
            try:
                await message.channel.send(
                    f"⚠️ **Cảnh báo Spam:** {message.author.mention}, bạn đang nhắn tin quá nhanh! Vui lòng làm chậm lại."
                )
            except Exception: pass
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
                except Exception: pass
                return True
                
        return False

async def setup(bot):
    await bot.add_cog(AIChatbot(bot))
