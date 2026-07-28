import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
import re
import requests
import shutil
from core.shared import config, music_queues, play_history, autoplay_disabled, YDL_OPTIONS, FFMPEG_OPTIONS, get_ffmpeg_executable

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
            
    @discord.ui.button(label="Hàng Đợi", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="m_queue")
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = interaction.guild.id
        if guild_id not in music_queues or not music_queues[guild_id]:
            return await interaction.response.send_message("📭 Hàng đợi hiện đang trống.", ephemeral=True)
        
        embed = discord.Embed(title="📜 Hàng Đợi Kế Tiếp", color=0x5865F2)
        q = music_queues[guild_id]
        for i, info in enumerate(q[:10]):
            try:
                duration = int(float(info.get('duration') or 0))
            except (ValueError, TypeError):
                duration = 0
            dur_str = f"{duration//60}:{duration%60:02d}" if duration else "Trực tiếp"
            embed.add_field(name=f"`#{i+1}` {info.get('title', 'Unknown')[:50]}", value=f"⏱ {dur_str} · 👤 {info.get('uploader', '?')}", inline=False)
        
        if len(q) > 10:
            embed.set_footer(text=f"Và {len(q)-10} bài khác nữa...")
        await interaction.response.send_message(embed=embed, ephemeral=True)
            
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
    try:
        duration = int(float(info.get('duration') or 0))
    except (ValueError, TypeError):
        duration = 0
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
        if not ctx.voice_client:
            return
        if guild_id in music_queues and len(music_queues[guild_id]) > 0:
            info = music_queues[guild_id].pop(0)
            play_history[guild_id] = info
            try:
                source = discord.FFmpegPCMAudio(info['url'], executable=get_ffmpeg_executable(), **FFMPEG_OPTIONS)
                ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
                coro = ctx.channel.send(embed=make_music_embed(info, "Hàng Đợi Kế Tiếp"), view=MusicControlView())
                asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            except Exception as e:
                print(f"[ERROR] Lỗi phát bài tiếp theo: {e}")
                coro = ctx.channel.send(f"❌ Không thể phát bài tiếp theo trong hàng đợi: {e}")
                asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        else:
            if guild_id in play_history and guild_id not in autoplay_disabled:
                last_song = play_history[guild_id]
                async def auto_play_task():
                    status_msg = await ctx.channel.send("🔍 Đang rà đài phát bài ngẫu nhiên cùng phân khúc...")
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
                                if ctx.voice_client:
                                    source = discord.FFmpegPCMAudio(next_info['url'], executable=get_ffmpeg_executable(), **FFMPEG_OPTIONS)
                                    ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
                                    await status_msg.edit(content=None, embed=make_music_embed(next_info, "🎵 Nhạc Đề Xuất (AutoPlay)"), view=MusicControlView())
                                    return
                    except Exception as e:
                        print(f"[ERROR] Lỗi tự động phát: {e}")
                    await status_msg.edit(content="⏸️ Hàng đợi trống. (Tạm tắt đề xuất do cạn kho nhạc tương thích).")
                asyncio.run_coroutine_threadsafe(auto_play_task(), self.bot.loop)

    @commands.hybrid_command(name=config.get("cmd_play", "play") or "play", aliases=["p"], description="Phát nhạc từ YouTube, SoundCloud...")
    async def play(self, ctx, *, search: str):
        if not ctx.author.voice: return await ctx.send("❌ Vào voice đi bạn ơi!")
        
        await ctx.defer()
        status_msg = await ctx.send("🔍 Đang khởi động hệ thống âm thanh...")
        
        vc = ctx.voice_client
        if vc:
            if not vc.is_connected():
                try: await vc.disconnect(force=True)
                except: pass
                try: vc = await ctx.author.voice.channel.connect(timeout=20.0)
                except Exception as e: return await status_msg.edit(content=f"❌ Lỗi kết nối: {e}")
            elif vc.channel != ctx.author.voice.channel:
                await vc.move_to(ctx.author.voice.channel)
        else:
            try:
                vc = await ctx.author.voice.channel.connect(timeout=20.0)
            except asyncio.TimeoutError:
                return await status_msg.edit(content="❌ **Lỗi Timeout:** Mạng đang bị nghẽn hoặc bot bị kẹt phiên cũ.\n👉 **Cách sửa:** Kích chuột phải vào bot ở Kênh Thoại -> Chọn **Ngắt kết nối** rồi gọi lại lệnh.")
            except Exception as e:
                return await status_msg.edit(content=f"❌ Lỗi tham gia kênh thoại: {e}")
                
        await status_msg.edit(content="📡 Đang tìm kiếm bài hát...")
        def fetch_youtube_data():
            nonlocal search
            raw_search = search.strip()
            
            # Xử lý Link Spotify: Lấy tên bài + ca sĩ từ Spotify API/oEmbed
            if "spotify.com" in raw_search and raw_search.startswith("http"):
                try:
                    sp_oembed = f"https://open.spotify.com/oembed?url={raw_search}"
                    r = requests.get(sp_oembed, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        title = data.get("title", "")
                        author = data.get("author_name", "")
                        if title:
                            raw_search = f"{title} {author}".strip()
                except Exception as e:
                    print(f"[Spotify Parse Warning] {e}")

            # Nếu là URL trực tiếp (YouTube, SoundCloud, TikTok, audio link...): Giữ nguyên URL cho yt-dlp
            if raw_search.startswith("http://") or raw_search.startswith("https://"):
                query = raw_search
            else:
                # Nếu là từ khóa tìm kiếm: Tìm kiếm top 1 kết quả trên YouTube
                query = f"ytsearch1:{raw_search}"
                
            try:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    return ydl.extract_info(query, download=False)
            except Exception as primary_e:
                err_str = str(primary_e).lower()
                if any(k in err_str for k in ["sign in", "bot", "confirm", "auth"]):
                    print(f"[YouTube Anti-Bot Fallback] Bị YouTube chặn IP bot, tự động chuyển fallback: {raw_search}")
                    fb_opts = dict(YDL_OPTIONS)
                    fb_opts['extractor_args'] = {'youtube': ['player_client=ios,mweb']}
                    fb_query = raw_search if raw_search.startswith("http") else f"scsearch1:{raw_search}"
                    try:
                        with yt_dlp.YoutubeDL(fb_opts) as ydl_fb:
                            return ydl_fb.extract_info(fb_query, download=False)
                    except Exception:
                        raise primary_e
                else:
                    raise primary_e
                
        try:
            results = await self.bot.loop.run_in_executor(None, fetch_youtube_data)
        except Exception as e:
            return await status_msg.edit(content=f"❌ Lỗi khi tìm kiếm hoặc phân tích bài hát: {e}")
            
        if not results: return await status_msg.edit(content=f"❌ Không tìm thấy bài hát nào!")
        
        guild_id = ctx.guild.id
        if guild_id not in music_queues: music_queues[guild_id] = []
        
        if 'entries' in results:
            if not results['entries']: return await status_msg.edit(content=f"❌ Không tìm được bài.")
            is_search = not search.startswith("http")
            entries_to_add = [results['entries'][0]] if is_search else results['entries']
            first_info = entries_to_add[0]
            playlist_title = results.get('title', 'Unknown Playlist')
            msg_text = "Danh Sách Chờ" if is_search else f"Playlist: {playlist_title}"
        else:
            entries_to_add = [results]
            first_info = results
            msg_text = "Danh Sách Chờ"
            
        for info in entries_to_add:
            if not info: continue
            if vc.is_playing() or vc.is_paused() or info != first_info:
                music_queues[guild_id].append(info)
                
        if not vc.is_playing() and not vc.is_paused():
            if not vc.is_connected():
                return await status_msg.edit(content="❌ Mất kết nối tới Kênh Thoại giữa chừng. Vui lòng gọi lại lệnh!")
            play_history[guild_id] = first_info
            
            try:
                ffmpeg_bin = get_ffmpeg_executable()
                source = discord.FFmpegPCMAudio(first_info['url'], executable=ffmpeg_bin, **FFMPEG_OPTIONS)
                vc.play(source, after=lambda e: self.play_next(ctx))
            except Exception as e:
                import os
                if os.name == 'nt' and not os.path.exists(ffmpeg_bin) and not shutil.which("ffmpeg"):
                    return await status_msg.edit(content="❌ **Thiếu file `ffmpeg.exe` trên máy Local Windows!**\n👉 Bạn cần tải file `ffmpeg.exe` đặt vào thư mục gốc của Bot (`d:\\Code\\Bot\\ffmpeg.exe`).")
                return await status_msg.edit(content=f"❌ Lỗi khởi chạy phát nhạc qua FFmpeg: {e}\n👉 Vui lòng kiểm tra lại đường dẫn ffmpeg hoặc link nhạc.")
                
            try:
                await status_msg.edit(content=None, embed=make_music_embed(first_info, "Bắt Đầu Phát"), view=MusicControlView())
            except Exception as e:
                print(f"[ERROR] Không hiển thị được embed bài hát: {e}")
                await ctx.send(f"🎶 **Bắt Đầu Phát:** {first_info.get('title', 'Unknown')}", view=MusicControlView())
                
            if len(entries_to_add) > 1:
                await ctx.channel.send(f"✅ Đã tải xong playlist **{playlist_title}** và đưa **{len(entries_to_add)-1}** bài còn lại vào hàng đợi!")
        else:
            pos = len(music_queues[guild_id]) - len(entries_to_add) + 1
            embed_title = f"{msg_text} (Vị trí thứ {pos})"
            try:
                await status_msg.edit(content=None, embed=make_music_embed(first_info, embed_title))
            except Exception as e:
                await ctx.send(f"➕ **Đã thêm vào hàng đợi:** {first_info.get('title', 'Unknown')} (Vị trí thứ {pos})")

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
            try:
                duration = int(float(info.get('duration') or 0))
            except (ValueError, TypeError):
                duration = 0
            dur_str = f"{duration//60}:{duration%60:02d}" if duration else "Trực tiếp"
            embed.add_field(name=f"`#{i+1}` {info.get('title', 'Unknown')[:50]}", value=f"⏱ {dur_str} · 👤 {info.get('uploader', '?')}", inline=False)
        
        if len(q) > 10:
            embed.set_footer(text=f"Và {len(q)-10} bài khác nữa...")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
