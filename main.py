import sys

# Configure stdout and stderr to use UTF-8 to prevent encoding errors on non-UTF-8 terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='ignore')

import discord
from discord.ext import commands, tasks
import asyncio
import json
import datetime
import os

try:
    from core.shared import config, api_server_started
    from core.database import cursor, conn, db_lock
    from core.api_server import start_api_server
    # Import Views for Persistent adding
    from cogs.music import MusicControlView
    from cogs.utilities import TicketView, TicketControlView, VoiceGeneratorView, PersistentRoleView
except Exception as e:
    import traceback
    print(f"❌ CRITICAL STARTUP ERROR (Import Failure): {e}")
    traceback.print_exc()
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.presences = True
proxy = os.environ.get("DISCORD_PROXY") or config.get("proxy") or None

def create_bot():
    """Tạo một Bot instance mới hoàn toàn (aiohttp session mới) để tránh lỗi 'Session is closed'."""
    _intents = discord.Intents.default()
    _intents.message_content = True
    _intents.members = True
    _intents.voice_states = True
    _intents.presences = True
    _bot = commands.Bot(
        command_prefix=config.get("prefix", "!"),
        intents=_intents,
        proxy=proxy
    )
    _bot.remove_command('help')
    return _bot

# Bot instance được tạo ban đầu, sẽ được thay thế sau mỗi lần kết nối thất bại
bot = create_bot()

async def export_server_data():
    import core.shared as shared
    server_data = {}
    for guild in bot.guilds:
        roles = [{"id": r.id, "name": r.name} for r in guild.roles if r.name != "@everyone"]
        channels = [{"id": c.id, "name": c.name} for c in guild.text_channels]
        categories = [{"id": c.id, "name": c.name} for c in guild.categories]
        server_data[str(guild.id)] = {"name": guild.name, "roles": roles, "channels": channels, "categories": categories}
    shared.server_data = server_data

@tasks.loop(minutes=1)
async def check_timed_roles():
    now = datetime.datetime.now().timestamp()
    def get_expired():
        with db_lock:
            cursor.execute("SELECT guild_id, user_id, role_id FROM timed_roles WHERE expires_at <= ?", (now,))
            return cursor.fetchall()
    expired = await bot.loop.run_in_executor(None, get_expired)
        
    for guild_id, user_id, role_id in expired:
        guild = bot.get_guild(int(guild_id))
        if guild:
            member = guild.get_member(int(user_id))
            role = guild.get_role(int(role_id))
            if member and role:
                try: await member.remove_roles(role)
                except: pass
    
    if expired:
        def delete_expired():
            with db_lock:
                cursor.executemany(
                    "DELETE FROM timed_roles WHERE guild_id=? AND user_id=? AND role_id=?",
                    expired
                )
                conn.commit()
        await bot.loop.run_in_executor(None, delete_expired)

@tasks.loop(seconds=3)
async def check_gui_tasks():
    def get_and_delete_tasks():
        with db_lock:
            cursor.execute("SELECT id, action, payload FROM gui_tasks")
            tasks_list = cursor.fetchall()
            for t in tasks_list:
                cursor.execute("DELETE FROM gui_tasks WHERE id=?", (t[0],))
            conn.commit()
            return tasks_list
    tasks_list = await bot.loop.run_in_executor(None, get_and_delete_tasks)
    
    for task_id, action, payload in tasks_list:
        try:
            if action == "SPAWN_RR_PANEL":
                data = json.loads(payload)
                guild_id = data.get("guild_id")
                channel_id = data.get("channel_id")
                title = data.get("title")
                roles_data = data.get("roles")
                
                guild = bot.get_guild(int(guild_id))
                if guild:
                    channel = guild.get_channel(int(channel_id))
                    if channel:
                        panel_desc = data.get("desc", "Nhấn vào các nút bên dưới để tự cấp / gỡ vai trò cho bản thân.")
                        embed = discord.Embed(
                            title=title,
                            description=panel_desc,
                            color=0x5865F2
                        )
                        for role_info in roles_data:
                            r_name = role_info.get("name", "?")
                            r_desc = role_info.get("desc", "")
                            field_val = f"• {r_desc}" if r_desc else "• Nhấn nút bên dưới để chọn."
                            embed.add_field(
                                name=f"◆  @{r_name}",
                                value=field_val,
                                inline=True
                            )
                        remainder = len(roles_data) % 3
                        if remainder == 1:
                            embed.add_field(name="\u200b", value="\u200b", inline=True)
                            embed.add_field(name="\u200b", value="\u200b", inline=True)
                        elif remainder == 2:
                            embed.add_field(name="\u200b", value="\u200b", inline=True)
                        
                        footer_text = data.get("footer", "❕ Nhấn nút để nhận thông báo và kết nối với cộng đồng server.")
                        embed.set_footer(text=footer_text)
                        
                        panel_id = str(int(datetime.datetime.now().timestamp() * 1000))
                        custom_id = f"rr_panel_{panel_id}"
                        view = PersistentRoleView(roles_data, custom_id)
                        await channel.send(embed=embed, view=view)
                        
                        with db_lock:
                            cursor.execute("INSERT INTO reaction_panels (message_id, guild_id, roles_json) VALUES (?, ?, ?)", 
                                           (panel_id, guild_id, json.dumps(roles_data)))
                            conn.commit()
        except Exception as e: print(f"Lỗi IPC: {e}")

def register_bot_events(b):
    """Gắn toàn bộ events và setup_hook vào một bot instance."""

    async def setup_hook():
        print("[THONG BAO] Đang tải các Cogs...")
        await b.load_extension("cogs.music")
        await b.load_extension("cogs.moderation")
        await b.load_extension("cogs.economy")
        await b.load_extension("cogs.utilities")
        await b.load_extension("cogs.social")
        await b.load_extension("cogs.welcome")
        await b.load_extension("cogs.ai_chatbot")
        print("[THONG BAO] Đã tải xong Cogs.")

        # Đăng ký các Persistent Views
        b.add_view(TicketView())
        b.add_view(TicketControlView())
        b.add_view(MusicControlView())
        b.add_view(VoiceGeneratorView())
        
        with db_lock:
            cursor.execute("SELECT message_id, roles_json FROM reaction_panels")
            panels = cursor.fetchall()
        for msg_id, rjson in panels:
            try:
                roles_data = json.loads(rjson)
                b.add_view(PersistentRoleView(roles_data, f"rr_panel_{msg_id}"))
            except: pass
            
        await b.tree.sync()

    b.setup_hook = setup_hook

    @b.event
    async def on_ready():
        print(f'[THONG BAO] Bot {b.user} da Started thanh cong!')
        if not check_timed_roles.is_running():
            check_timed_roles.start()
        if not check_gui_tasks.is_running():
            check_gui_tasks.start()
        await export_server_data()
        print("[THONG BAO] Da cap nhat danh sach Role va Channel moi nhat.")

    @b.event
    async def on_guild_join(g): await export_server_data()
    @b.event
    async def on_guild_remove(g): await export_server_data()
    @b.event
    async def on_guild_role_create(r): await export_server_data()
    @b.event
    async def on_guild_role_update(bef, aft): await export_server_data()
    @b.event
    async def on_guild_channel_create(c): await export_server_data()
    @b.event
    async def on_guild_channel_update(bef, aft): await export_server_data()

    @b.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound): return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Bạn không có quyền thực hiện lệnh này.")
            return
        print(f"[LOI LENH] {error}")

# Gắn events cho bot instance khởi tạo ban đầu
register_bot_events(bot)

async def main():
    global bot

    import core.shared as shared

    # 1. Lấy token
    token = os.environ.get("DISCORD_TOKEN") or config.get("token")
    if not token:
        print("[LOI] Chua cau hinh DISCORD_TOKEN trong .env hoac config.json!")
        sys.exit(1)

    # 2. Khởi động HTTP API server ngay lập tức để Render nhận diện port
    if not shared.api_server_started:
        print("[THONG BAO] Dang khoi dong HTTP API server...")
        asyncio.create_task(start_api_server(bot))
        shared.api_server_started = True

    # 3. Vòng lặp kết nối — tạo lại Bot instance mới sau mỗi lần thất bại
    retry_delay = 5
    attempt = 0
    while True:
        attempt += 1
        try:
            print(f"[THONG BAO] Dang ket noi den Discord API... (lan thu {attempt})")
            await bot.start(token)
            # Thoát vòng lặp nếu bot chạy xong bình thường (ví dụ bị tắt thủ công)
            break
        except discord.errors.HTTPException as e:
            if e.status == 429:
                # Discord trả về thời gian retry nếu là rate limit thông thường
                # error code 0 là CloudFlare block — không có retry_after, dùng backoff
                retry_after = getattr(e, "retry_after", None)
                if retry_after and retry_after > 0:
                    wait = retry_after
                else:
                    wait = retry_delay
                print(f"[LOI 429] IP bi Discord block. Cho {wait:.0f} giay truoc khi thu lai. (lan {attempt})")
                retry_delay = max(retry_delay, int(wait))
                await asyncio.sleep(wait)
            else:
                print(f"[LOI HTTP {e.status}] {e}. Thu lai sau {retry_delay} giay.")
                await asyncio.sleep(retry_delay)
        except discord.errors.LoginFailure as e:
            print(f"[LOI TOKEN] Token khong hop le: {e}. Dung chuong trinh.")
            sys.exit(1)
        except Exception as e:
            print(f"[LOI BAT THUONG] {e}. Thu lai sau {retry_delay} giay.")
            await asyncio.sleep(retry_delay)

        # Đóng sạch bot cũ
        try:
            await bot.close()
        except Exception:
            pass

        # Tạo Bot instance hoàn toàn mới (aiohttp session mới)
        bot = create_bot()
        register_bot_events(bot)

        # Cập nhật bot reference trong API server
        try:
            from core import api_server as _api_mod
            if hasattr(_api_mod, '_app') and _api_mod._app is not None:
                _api_mod._app["bot"] = bot
        except Exception:
            pass

        retry_delay = min(retry_delay * 2, 300)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[THONG BAO] Bot duoc dung boi nguoi dung.")