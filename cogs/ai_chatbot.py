# Updated by duynguyen1012 (AI/ML Engineer)
import discord
from discord.ext import commands
import google.generativeai as genai
import os

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Chi tra loi neu bot duoc mention hoac tin nhan gui vao kenh AI chat duoc cau hinh
        is_mentioned = self.bot.user in message.mentions
        
        # Doc kenh AI tu config
        from core.shared import config
        ai_channel_id = config.get("ai_channel_id")
        is_ai_channel = ai_channel_id and str(message.channel.id) == str(ai_channel_id)

        if is_mentioned or is_ai_channel:
            # Xoa mention khoi content
            content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not content:
                await message.reply("Xin chào! Bạn có thể đặt câu hỏi cho tôi bằng cách nhắn tin trực tiếp tại đây.")
                return

            if not self.model:
                await message.reply("⚠️ Tính năng AI Chatbot chưa được cấu hình API Key (GEMINI_API_KEY). Vui lòng liên hệ Admin!")
                return

            async with message.channel.typing():
                try:
                    # Chạy trong executor để tránh blocking event loop vì gemini-pro api đồng bộ
                    loop = self.bot.loop
                    response = await loop.run_in_executor(
                        None, 
                        lambda: self.model.generate_content(content)
                    )
                    reply_text = response.text
                    # Gioi han 2000 ky tu cua Discord
                    if len(reply_text) > 2000:
                        reply_text = reply_text[:1990] + "..."
                    await message.reply(reply_text)
                except Exception as e:
                    print(f"[AI Error] Loi khi goi Gemini API: {e}")
                    await message.reply("❌ Đã xảy ra lỗi khi kết nối với AI. Vui lòng thử lại sau.")

async def setup(bot):
    await bot.add_cog(AIChatbot(bot))
