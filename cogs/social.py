import discord
from discord.ext import commands, tasks
import re
import requests
import xml.etree.ElementTree as ET
from core.shared import config, PLATFORM_EMOJI
from core.database import cursor, conn, db_lock
import json

class DoiLinkView(discord.ui.View):
    def __init__(self, platform, link):
        super().__init__(timeout=None)
        emoji = PLATFORM_EMOJI.get(platform, "🔗")
        self.add_item(discord.ui.Button(label=f"Xem trực tiếp trên {platform.capitalize()}", url=link, emoji=emoji))

def is_mod():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator: return True
        guild_id = str(ctx.guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)
        mod_role_ids = server_cfg.get("mod_role_ids", [])
        old_mod = server_cfg.get("mod_role_id")
        if old_mod and str(old_mod) not in [str(x) for x in mod_role_ids]:
            mod_role_ids = list(mod_role_ids) + [old_mod]
        if not mod_role_ids: return False
        user_role_ids = [r.id for r in ctx.author.roles]
        return any(int(m) in user_role_ids for m in mod_role_ids)
    return commands.check(predicate)


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not self.social_media_loop.is_running():
            self.social_media_loop.start()

    def cog_unload(self):
        self.social_media_loop.cancel()

    @tasks.loop(minutes=5)
    async def social_media_loop(self):
        with db_lock:
            cursor.execute("SELECT guild_id, platform, target_id, channel_id, ping_role, last_post_id FROM social_tracker")
            rows = cursor.fetchall()
            
        for guild_id, platform, target_id, channel_id, ping_role, last_post_id in rows:
            channel = self.bot.get_channel(int(channel_id))
            if not channel: continue
            new_post_id = last_post_id
            post_data = None
            
            try:
                if platform == "youtube":
                    def _fetch_yt(): return requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={target_id}", timeout=10)
                    resp = await self.bot.loop.run_in_executor(None, _fetch_yt)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        ns = {'yt': 'http://www.youtube.com/xml/schemas/2015', 'ns': 'http://www.w3.org/2005/Atom'}
                        entry = root.find('ns:entry', ns)
                        if entry is not None:
                            video_id = entry.find('yt:videoId', ns).text
                            if video_id != last_post_id:
                                new_post_id = video_id
                                title = entry.find('ns:title', ns).text
                                author = entry.find('ns:author/ns:name', ns).text
                                link = entry.find('ns:link', ns).attrib['href']
                                mgrp = entry.find('{http://search.yahoo.com/mrss/}group')
                                thumb_el = mgrp.find('{http://search.yahoo.com/mrss/}thumbnail') if mgrp else None
                                thumbnail = thumb_el.attrib['url'] if thumb_el is not None else ""
                                post_data = {
                                    "title": f"🎥 {author} vừa ra video mới!",
                                    "desc": f"**{title}**\n\n👇 Ấn vào liên kết dưới để xem ngay!",
                                    "url": link, "color": 0xFF0000, "image": thumbnail
                                }
                elif platform == "reddit":
                    def _fetch_reddit(): return requests.get(f"https://www.reddit.com/r/{target_id}/new.json?limit=1", headers={"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
                    resp = await self.bot.loop.run_in_executor(None, _fetch_reddit)
                    if resp.status_code == 200:
                        data = resp.json()
                        children = data.get("data", {}).get("children", [])
                        if children:
                            post = children[0]["data"]
                            if post["id"] != last_post_id:
                                new_post_id = post["id"]
                                link = f"https://reddit.com{post['permalink']}"
                                img = post.get("url_overridden_by_dest", "")
                                if not img.endswith(('.png', '.jpg', '.jpeg', '.gif')): img = ""
                                post_data = {
                                    "title": f"🟧 Cập nhật r/{target_id} Mới Nóng Hổi!",
                                    "desc": f"**{post['title']}**\n✍️ Bởi u/{post['author']}\n\n👇 Nhanh tay vào đọc ngay!",
                                    "url": link, "color": 0xFF4500, "image": img
                                }

                elif platform == "tiktok":
                    rss_url = f"https://rsshub.app/tiktok/user/@{target_id}"
                    def _fetch_tiktok(): return requests.get(rss_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                    resp = await self.bot.loop.run_in_executor(None, _fetch_tiktok)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        chan = root.find('channel')
                        item = chan.find('item') if chan is not None else None
                        if item is not None:
                            vid_link = item.findtext('link', '')
                            vid_id = vid_link.split('/')[-1].split('?')[0]
                            if vid_id and vid_id != last_post_id:
                                new_post_id = vid_id
                                vid_title = item.findtext('title', 'Video mới')
                                enclosure = item.find('enclosure')
                                thumb = enclosure.attrib.get('url', '') if enclosure is not None else ''
                                if not thumb:
                                    desc_text = item.findtext('description', '')
                                    m_img = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_text)
                                    if m_img: thumb = m_img.group(1)
                                post_data = {
                                    "title": f"🎵 @{target_id} vừa đăng video TikTok mới!",
                                    "desc": f"**{vid_title}**\n\n👇 Ấn vào xem ngay!",
                                    "url": vid_link, "color": 0x010101, "image": thumb
                                }

                elif platform == "facebook":
                    def _fetch_fb(): return requests.get(target_id, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                    resp = await self.bot.loop.run_in_executor(None, _fetch_fb)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        ns_atom = {'a': 'http://www.w3.org/2005/Atom'}
                        entry = root.find('a:entry', ns_atom)
                        if entry is None:
                            chan = root.find('channel')
                            entry = chan.find('item') if chan else None
                            if entry is not None:
                                post_link = entry.findtext('link', '')
                                post_id = entry.findtext('guid', post_link)
                                post_title = entry.findtext('title', 'Bài viết mới')
                                desc_raw = entry.findtext('description', '')
                            else: post_link = post_id = post_title = desc_raw = None
                        else:
                            post_link = entry.findtext('a:link', '', ns_atom) or (entry.find('a:link', ns_atom).attrib.get('href','') if entry.find('a:link', ns_atom) is not None else '')
                            post_id = entry.findtext('a:id', post_link, ns_atom)
                            post_title = entry.findtext('a:title', 'Bài viết mới', ns_atom)
                            desc_raw = entry.findtext('a:summary', '', ns_atom)
                        
                        if post_id and post_id != last_post_id:
                            new_post_id = post_id
                            m_img = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_raw or '')
                            thumb = m_img.group(1) if m_img else ''
                            post_data = {
                                "title": "🔵 Bài viết Facebook mới!",
                                "desc": f"**{post_title}**\n\n👇 Xem trực tiếp tại đây!",
                                "url": post_link, "color": 0x1877F2, "image": thumb
                            }
                                
                if post_data and new_post_id != last_post_id:
                    embed = discord.Embed(title=post_data["title"], description=post_data["desc"], color=post_data["color"])
                    if post_data["image"]: embed.set_image(url=post_data["image"])
                    await channel.send(content=ping_role if ping_role else "", embed=embed, view=DoiLinkView(platform, post_data["url"]))
                    with db_lock:
                        cursor.execute("UPDATE social_tracker SET last_post_id=? WHERE guild_id=? AND platform=? AND target_id=?", (new_post_id, guild_id, platform, target_id))
                        conn.commit()
            except Exception as e:
                print(f"[Loop] Lỗi Radar {platform} tại {target_id}: {e}")

    @social_media_loop.before_loop
    async def before_social_media_loop(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="add_social")
    @is_mod()
    async def add_social(self, ctx, platform: str, target: str, channel: discord.TextChannel = None, ping_role: discord.Role = None):
        platform = platform.lower()
        SUPPORTED = ["youtube", "reddit", "tiktok", "facebook"]
        if platform not in SUPPORTED: return await ctx.send(f"❌ Máy quét chỉ bắt sóng: `{'`, `'.join(SUPPORTED)}`.")
        channel = channel or ctx.channel
        target_id = target
        
        if platform == "youtube":
            if "youtube.com" in target or "youtu.be" in target:
                m = re.search(r'youtube\.com/channel/(UC[\w-]+)', target)
                if m: target_id = m.group(1)
                else:
                    resp = requests.get(target, timeout=10)
                    m2 = re.search(r'channel_id=([\w-]+)', resp.text)
                    if m2: target_id = m2.group(1)
                    else: return await ctx.send("❌ Thất bại: Không thu thập được Channel ID ẩn của liên kết YouTube này.")
        elif platform == "reddit":
            if "reddit.com/r/" in target:
                target_id = target.split("reddit.com/r/")[1].split("/")[0]
        elif platform == "tiktok":
            target_id = target.lstrip("@").split("/")[-1].split("?")[0]
        elif platform == "facebook":
            await ctx.send("⚠️ **Lưu ý Facebook:** Facebook chặn truy cập thẳng nên bạn cần dùng dịch vụ tạo RSS trước:\n> 1. Vào **rss.app** hoặc **rssbridge** để tạo RSS Link từ trang Facebook.\n> 2. Dán URL RSS vừa tạo làm giá trị āng-ten (target).\nBot sẽ quét RSS link đó mỗi 5 phút.")
            target_id = target
                
        ping_str = ping_role.mention if ping_role else ""
        with db_lock:
            cursor.execute("INSERT OR REPLACE INTO social_tracker (guild_id, platform, target_id, channel_id, ping_role, last_post_id) VALUES (?, ?, ?, ?, ?, ?)", 
                          (str(ctx.guild.id), platform, target_id, str(channel.id), ping_str, "NO_POST_YET"))
            conn.commit()
        await ctx.send(f"✅ Đã cắm Ăng-ten sóng **{platform.upper()}** (ID: `{target_id}`)! Hễ rục rịch là Bot réo tại {channel.mention}.")

    @commands.hybrid_command(name="rm_social")
    @is_mod()
    async def rm_social(self, ctx, platform: str, target_id: str):
        with db_lock:
            cursor.execute("DELETE FROM social_tracker WHERE guild_id=? AND platform=? AND target_id=?", (str(ctx.guild.id), platform.lower(), target_id))
            conn.commit()
        await ctx.send(f"🗑️ Đã nhổ Ăng-ten **{platform.upper()}** (ID: `{target_id}`). Ngừng theo dõi.")

    @commands.hybrid_command(name="list_social")
    async def list_social(self, ctx):
        with db_lock:
            cursor.execute("SELECT platform, target_id, channel_id FROM social_tracker WHERE guild_id=?", (str(ctx.guild.id),))
            rows = cursor.fetchall()
        if not rows: return await ctx.send("📡 Trạm vô tuyến hiện tại đang rống. Chưa chĩa chảo thu sóng nào.")
        msg = "📡 **CÁC THỤ THỂ RADAR ĐANG BẮT SÓNG TRONG MÁY CHỦ:**\n\n"
        for r in rows:
            c = self.bot.get_channel(int(r[2]))
            msg += f"• **{r[0].capitalize()}** `[ID: {r[1]}]` ➡ Rót bài vào: {c.mention if c else 'Rác'}\n"
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Social(bot))
