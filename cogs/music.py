import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
import re
import requests
from core.shared import config, music_queues, play_history, autoplay_disabled, YDL_OPTIONS, FFMPEG_OPTIONS

class MusicControlView(discord.ui.View):
    def __init__(self): 
        super().__init__(timeout=None)
        
    async def interaction_check(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ Bot hiện không ở trong kênh thoại nào.", ephemeral=True)
            return False
        if not interaction.user.voice or interaction.user.voice.channel != vc.channel:
            await interaction.response.send_message("❌ Bạn phải vào chung Kênh Thoại với Bot thì mới được bấm!", ephemeral=True)
            return False
        return True
        
    @discord.ui.button(label="Tạm Dừng / Phát", style=discord.ButtonStyle.primary, emoji="⏸️", custom_id="m_pause")
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing(): 
            vc.pause()
            await interaction.response.send_message("⏸️ Đã tạm dừng nhạc.", ephemeral=False)
        elif vc and vc.is_paused(): 
            vc.resume()
            await interaction.response.send_message("▶️ Tiếp tục phát nhạc.", ephemeral=False)
        else: 
            await interaction.response.send_message("❌ Chưa đến lượt.", ephemeral=True)
            
    @discord.ui.button(label="Bỏ Qua", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="m_skip")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing(): 
            vc.stop()
            await interaction.response.send_message("⏭️ Tiến lên bài tiếp theo!", ephemeral=False)
            
    @discord.ui.button(label="Tắt Nhạc", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="m_stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            music_queues.pop(interaction.guild.id, None)
            vc.stop()
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Đã giải phóng kênh thoại.", ephemeral=False)
            
    @discord.ui.button(label="Trộn Bài", style=discord.ButtonStyle.success, emoji="🔀", custom_id="m_shuffle")
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        if guild_id in music_queues and len(music_queues[guild_id]) > 1:
            random.shuffle(music_queues[guild_id])
            await interaction.response.send_message(f"🔀 Đã xáo trộn ngẫu nhiên {len(music_queues[guild_id])} bài trong danh sách chờ!", ephemeral=False)
        else:
            await interaction.response.send_message("❌ Hàng đợi phải có từ 2 bài trở lên mới đảo thuật toán được.", ephemeral=True)
            
    @discord.ui.button(label="Tự Động Phát", style=discord.ButtonStyle.secondary, emoji="🎲", custom_id="m_autoplay")
    async def autoplay_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        if guild_id in autoplay_disabled:
            autoplay_disabled.remove(guild_id)
            await interaction.response.send_message("✅ Đã **BẬT** Tự động phát nhạc (AutoPlay). Sẽ tự chọn bài nã tiếp khi hết danh sách!", ephemeral=False)
        else:
            autoplay_disabled.add(guild_id)
            await interaction.response.send_message("🛑 Đã **TẮT** Tự động phát nhạc (AutoPlay). Nhạc sẽ dừng khi hết hàng đợi.", ephemeral=False)

def make_music_embed(info, title="Đang Phát"):
    duration = info.get('duration', 0)
    minutes, seconds = divmod(duration, 60)
    embed = discord.Embed(title=f"🎶 {title}", description=f"**[{info.get('title')}]({info.get('webpage_url', '')})**", color=0x5865F2)
    if 'thumbnail' in info: embed.set_thumbnail(url=info['thumbnail'])
    embed.add_field(name="⏱️ Thời lượng", value=f"{minutes}:{seconds:02d}" if duration else "Phát Trực Tiếp")
    embed.add_field(name="👤 Kênh", value=info.get('uploader', 'Không xác định'))
    return embed

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def play_next(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in music_queues and len(music_queues[guild_id]) > 0:
            info = music_queues[guild_id].pop(0)
            play_history[guild_id] = info
            source = discord.FFmpegPCMAudio(info['url'], executable=config.get("ffmpeg_path", "./ffmpeg.exe"), **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
            coro = ctx.send(embed=make_music_embed(info, "Hàng Đợi Kế Tiếp"), view=MusicControlView())
            asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        else:
            if guild_id in play_history and guild_id not in autoplay_disabled:
                last_song = play_history[guild_id]
                async def auto_play_task():
                    status_msg = await ctx.send("🔍 Đang rà đài phát bài ngẫu nhiên cùng phân khúc...")
                    def fetch_related():
                        q = f"ytsearch10:{last_song.get('uploader', '')} {last_song.get('title', '').split()[0]} tracks"
                        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                            return ydl.extract_info(q, download=False)
                    try:
                        results = await self.bot.loop.run_in_executor(None, fetch_related)
                        if 'entries' in results and len(results['entries']) > 0:
                            candidates = [e for e in results['entries'] if e.get('id') != last_song.get('id')]
                            if len(candidates) > 0:
                                next_info = random.choice(candidates)
                                play_history[guild_id] = next_info
                                source = discord.FFmpegPCMAudio(next_info['url'], executable=config.get("ffmpeg_path", "./ffmpeg.exe"), **FFMPEG_OPTIONS)
                                ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
                                await status_msg.edit(content=None, embed=make_music_embed(next_info, "🎵 Nhạc Đề Xuất (AutoPlay)"), view=MusicControlView())
                                return
                    except:
                        pass
                    await status_msg.edit(content="⏸️ Hàng đợi trống. (Tạm tắt đề xuất do cạn kho nhạc tương thích).")
                asyncio.run_coroutine_threadsafe(auto_play_task(), self.bot.loop)

    @commands.hybrid_command(name=config.get("cmd_play", "play") or "play")
    async def play(self, ctx, *, search: str):
        if not ctx.author.voice: return await ctx.send("Vào voice đi bạn ơi!")
        
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            vc = ctx.voice_client
        else:
            try:
                vc = await ctx.author.voice.channel.connect(timeout=20.0)
            except asyncio.TimeoutError:
                return await ctx.send("❌ **Lỗi Timeout:** Mạng đang bị nghẽn hoặc bot bị kẹt phiên cũ.\n👉 **Cách sửa 1:** Kích chuột phải vào bot ở Kênh Thoại -> Chọn **Ngắt kết nối (Disconnect)** rồi gọi lại lệnh.\n👉 **Cách sửa 2:** Đổi Region (Vùng) của Kênh Thoại sang khu vực khác (Automatic, US hoặc Japan)!")
            except Exception as e:
                return await ctx.send(f"❌ Lỗi tham gia kênh thoại: {e}")
            
        async with ctx.typing():
            status_msg = await ctx.send("🔍 Đang kết nối với vệ tinh âm thanh...")
            def fetch_youtube_data():
                nonlocal search
                if "spoti" in search and search.startswith("http"):
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                        html = requests.get(search, headers=headers, timeout=5).text
                        t_match = re.search(r'<title>(.*?)</title>', html)
                        if t_match:
                            title_text = t_match.group(1).replace(" - song and lyrics by ", " ")
                            title_text = re.sub(r' \| Spotify$', '', title_text).replace("&#39;", "'").replace("&amp;", "&")
                            search = title_text.strip()
                        else: search = "Spotify unsupported DRM track"
                    except: search = "Spotify fallback error"
                
                query = f"ytsearch:{search}" if not search.startswith("http") else search
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl: return ydl.extract_info(query, download=False)
                    
            results = await self.bot.loop.run_in_executor(None, fetch_youtube_data)
            if not results: return await status_msg.edit(content=f"❌ Không tìm thấy bài hát nào!")
            
            if 'entries' in results:
                if len(results['entries']) == 0: return await status_msg.edit(content=f"❌ Không tìm được bài.")
                info = results['entries'][0]
            else:
                info = results
                
        guild_id = ctx.guild.id
        if guild_id not in music_queues: music_queues[guild_id] = []
        
        if vc.is_playing() or vc.is_paused():
            music_queues[guild_id].append(info)
            await status_msg.edit(content=None, embed=make_music_embed(info, f"Danh Sách Chờ (Vị trí thứ {len(music_queues[guild_id])})"))
        else:
            play_history[guild_id] = info
            vc.play(discord.FFmpegPCMAudio(info['url'], executable=config.get("ffmpeg_path", "./ffmpeg.exe"), **FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
            await status_msg.edit(content=None, embed=make_music_embed(info, "Bắt Đầu Phát"), view=MusicControlView())

    @commands.hybrid_command(name=config.get("cmd_skip", "skip") or "skip")
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Đã nhảy bài!")

    @commands.hybrid_command(name=config.get("cmd_pause", "pause") or "pause")
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Đứng hình mất 5 giây! (Đã Tạm Dừng)")

    @commands.hybrid_command(name=config.get("cmd_resume", "resume") or "resume")
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Dẩy lên nào! (Đã Phát Tiếp)")

    @commands.hybrid_command(name=config.get("cmd_stop", "stop") or "stop")
    async def stop(self, ctx):
        if ctx.guild.id in music_queues: music_queues[ctx.guild.id].clear()
        if ctx.voice_client: 
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Đã cháy máy. Rút phích cắm!")

    @commands.hybrid_command(name="queue", description="Xem danh sách bài đang chờ phát.")
    async def queue_cmd(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in music_queues or not music_queues[guild_id]:
            return await ctx.send("📭 Hàng đợi hiện đang trống.")
        
        embed = discord.Embed(title="📜 Hàng Đợi Kế Tiếp", color=0x5865F2)
        q = music_queues[guild_id]
        for i, info in enumerate(q[:10]):
            duration = info.get('duration', 0)
            dur_str = f"{duration//60}:{duration%60:02d}" if duration else "Trực tiếp"
            embed.add_field(name=f"`#{i+1}` {info.get('title', 'Unknown')[:50]}", value=f"⏱ {dur_str} · 👤 {info.get('uploader', '?')}", inline=False)
        
        if len(q) > 10:
            embed.set_footer(text=f"Và {len(q)-10} bài khác nữa...")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
