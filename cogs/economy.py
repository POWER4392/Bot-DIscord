import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import random
import os
import time
from core.shared import config, level_cooldown
from core.database import cursor, db_lock, db_get_user, db_update_xp

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        guild_id = str(message.guild.id) if message.guild else None
        if not guild_id: return

        user_id = str(message.author.id)
        current_time = time.time()
        
        if user_id not in level_cooldown or current_time - level_cooldown[user_id] >= 60:
            level_cooldown[user_id] = current_time
            await self.bot.loop.run_in_executor(None, db_get_user, guild_id, user_id)
            earned_xp = random.randint(15, 25)
            old_level, new_level = await self.bot.loop.run_in_executor(None, db_update_xp, guild_id, user_id, earned_xp)
            
            if new_level > old_level:
                await message.channel.send(f"🎉 Chúc mừng {message.author.mention}! Cày cuốc chăm chỉ đã giúp bạn đột phá lên **Cấp {new_level}**! 🚀 (+{earned_xp} XP)")

    @commands.hybrid_command(name="top", description="Bảng xếp hạng XP Top 10 của Server.")
    async def leaderboard(self, ctx):
        guild_id = str(ctx.guild.id)
        def fetch_leaderboard():
            with db_lock:
                cursor.execute("SELECT user_id, xp, level FROM users WHERE guild_id=? ORDER BY xp DESC LIMIT 10", (guild_id,))
                return cursor.fetchall()
        rows = await self.bot.loop.run_in_executor(None, fetch_leaderboard)
        if not rows:
            return await ctx.send("📊 Chưa có ai tích lũy XP trên server này!")
        
        embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG XP SERVER", color=0xF1C40F)
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, xp, lvl) in enumerate(rows):
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"User#{uid[-4:]}"
            desc += f"{medal} **{name}** — Cấp **{lvl}** · `{xp:,} XP`\n"
        embed.description = desc
        embed.set_footer(text=f"Top 10 thành viên tích cực nhất · {ctx.guild.name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name=config.get("cmd_rank", "rank") or "rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        current_data = await self.bot.loop.run_in_executor(None, db_get_user, guild_id, user_id)
        xp, level = current_data[0], current_data[1]
        
        next_level_xp = int(100 * (level ** 1.5)) + 100
        
        sorted_users = []
        def fetch_sorted_users():
            with db_lock:
                cursor.execute("SELECT user_id, xp FROM users WHERE guild_id=? ORDER BY xp DESC", (guild_id,))
                return cursor.fetchall()
        sorted_users = await self.bot.loop.run_in_executor(None, fetch_sorted_users)
            
        rank_pos = next((i + 1 for i, row in enumerate(sorted_users) if row[0] == str(member.id)), "?")

        async with ctx.typing():
            bg = Image.new("RGBA", (800, 250), (43, 45, 49, 255))
            try:
                response = requests.get(member.display_avatar.url)
                avatar = Image.open(BytesIO(response.content)).convert("RGBA").resize((180, 180))
                mask = Image.new("L", (180, 180), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 180, 180), fill=255)
                bg.paste(avatar, (35, 35), mask)
            except: pass
            
            draw = ImageDraw.Draw(bg)
            try: 
                font_path = config.get("servers", {}).get(guild_id, {}).get("font_file", "")
                if not os.path.exists(font_path): raise Exception
                font_l, font_s = ImageFont.truetype(font_path, 48), ImageFont.truetype(font_path, 28)
            except: 
                font_l = font_s = ImageFont.load_default()
            
            draw.text((250, 40), str(member.name), font=font_l, fill=(255, 255, 255))
            draw.text((250, 100), f"Rank: #{rank_pos}  |  Level: {level}", font=font_s, fill=(185, 187, 190))
            
            bar_x, bar_y, bar_w, bar_h = 250, 170, 500, 30
            draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=15, fill=(64, 68, 75))
            
            current_lvl_xp = int(100 * ((level-1) ** 1.5)) if level > 1 else 0
            xp_in_level = max(0, xp - current_lvl_xp)
            xp_needed = max(1, next_level_xp - current_lvl_xp)
            progress = min(1.0, xp_in_level / xp_needed)
            fill_w = max(30, int(bar_w * progress))
            draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=15, fill=(88, 101, 242))
            draw.text((bar_x + bar_w - 200, bar_y - 35), f"{xp} / {next_level_xp} XP", font=font_s, fill=(255, 255, 255))

            with BytesIO() as image_binary:
                bg.save(image_binary, "PNG")
                image_binary.seek(0)
                await ctx.send(file=discord.File(fp=image_binary, filename="rank.png"))

    @commands.hybrid_command(name=config.get("cmd_profile", "profile") or "profile")
    async def profile_cmd(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        guild_id, user_id = str(ctx.guild.id), str(member.id)
        data = await self.bot.loop.run_in_executor(None, db_get_user, guild_id, user_id)
        xp, level = data[0], data[1]
        
        next_level_xp = int(100 * (level ** 1.5)) + 100
        current_lvl_xp = int(100 * ((level - 1) ** 1.5)) if level > 1 else 0
        xp_in_level = max(0, xp - current_lvl_xp)
        xp_needed = max(1, next_level_xp - current_lvl_xp)
        progress_pct = min(100, int(xp_in_level / xp_needed * 100))
        bar_filled = int(progress_pct / 10)
        bar = "\u2588" * bar_filled + "\u2591" * (10 - bar_filled)
        
        embed = discord.Embed(title=f"\ud83c\udfc6 H\u1ed3 S\u01a1 c\u1ee7a {member.display_name}", color=0x5865F2)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="\ud83c\udf1f Level", value=f"**{level}**", inline=True)
        embed.add_field(name="\u26a1 XP", value=f"**{xp:,}** XP", inline=True)
        embed.add_field(name="\ud83d\udcca Ti\u1ebfn \u0111\u1ed9", value=f"`{bar}` {progress_pct}%\n({xp_in_level}/{xp_needed} XP \u0111\u1ebfn c\u1ea5p {level+1})", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
