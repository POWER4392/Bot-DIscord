import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import random
import os
import time
from core.shared import config, level_cooldown
from core.database import cursor, db_lock, db_get_user, db_update_xp, xp_for_level, level_for_xp

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
            old_level, new_level, total_xp = await self.bot.loop.run_in_executor(None, db_update_xp, guild_id, user_id, earned_xp)
            
            if new_level > old_level:
                next_lvl_xp = xp_for_level(new_level + 1)
                embed = discord.Embed(
                    title="🎉 ĐỘT PHÁ CẤP ĐỘ! (LEVEL UP)",
                    description=f"Chúc mừng {message.author.mention} đã cày cuốc chăm chỉ và thăng cấp thành công!",
                    color=0xF1C40F
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                embed.add_field(name="⭐ Cấp độ", value=f"**Cấp {old_level}** ➔ **Cấp {new_level}**", inline=True)
                embed.add_field(name="⚡ Tổng XP", value=f"**{total_xp:,}** XP *(+{earned_xp} XP)*", inline=True)
                embed.add_field(name="🎯 Cấp tiếp theo", value=f"**{next_lvl_xp:,}** XP", inline=False)
                
                footer_icon = message.guild.icon.url if (message.guild and message.guild.icon) else None
                guild_name = message.guild.name if message.guild else "Server"
                embed.set_footer(text=f"Server: {guild_name} • Tiếp tục tương tác để nhận thêm XP!", icon_url=footer_icon)
                
                await message.channel.send(embed=embed)

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
        
        current_lvl_xp = xp_for_level(level)
        next_lvl_xp = xp_for_level(level + 1)
        
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
                def _fetch_avatar():
                    return requests.get(member.display_avatar.url, timeout=10)
                avatar_resp = await self.bot.loop.run_in_executor(None, _fetch_avatar)
                avatar = Image.open(BytesIO(avatar_resp.content)).convert("RGBA").resize((180, 180))
                mask = Image.new("L", (180, 180), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 180, 180), fill=255)
                bg.paste(avatar, (35, 35), mask)
            except Exception as e:
                print(f"[Rank] Loi tai avatar: {e}")
            
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
            
            xp_in_level = max(0, xp - current_lvl_xp)
            xp_needed = max(1, next_lvl_xp - current_lvl_xp)
            progress = min(1.0, xp_in_level / xp_needed)
            fill_w = max(30, int(bar_w * progress)) if progress > 0 else 0
            if fill_w > 0:
                draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=15, fill=(88, 101, 242))
            
            draw.text((bar_x + bar_w - 200, bar_y - 35), f"{xp:,} / {next_lvl_xp:,} XP", font=font_s, fill=(255, 255, 255))

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
        
        current_lvl_xp = xp_for_level(level)
        next_lvl_xp = xp_for_level(level + 1)
        xp_in_level = max(0, xp - current_lvl_xp)
        xp_needed = max(1, next_lvl_xp - current_lvl_xp)
        progress_pct = min(100, int(xp_in_level / xp_needed * 100))
        bar_filled = int(progress_pct / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        
        embed = discord.Embed(title=f"🏆 Hồ Sơ của {member.display_name}", color=0x5865F2)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🌟 Level", value=f"**{level}**", inline=True)
        embed.add_field(name="⚡ XP", value=f"**{xp:,}** XP", inline=True)
        embed.add_field(name="📊 Tiến độ", value=f"`{bar}` {progress_pct}%\n({xp:,}/{next_lvl_xp:,} XP đến cấp {level+1})", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))

