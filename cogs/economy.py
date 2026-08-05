import discord
from discord.ext import commands
import random
import time
from core.shared import config, level_cooldown
from core.database import cursor, db_lock, db_get_user, db_update_xp, xp_for_level

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

