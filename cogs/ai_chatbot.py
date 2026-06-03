import discord
from discord.ext import commands
import google.generativeai as genai
import os

class AIChatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        # TODO: Implement Gemini conversation logic here
        pass

async def setup(bot):
    await bot.add_cog(AIChatbot(bot))
