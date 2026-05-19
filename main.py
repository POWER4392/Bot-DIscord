import discord
from discord.ext import commands, tasks
import asyncio
import json
import datetime
import os
import sys

from core.shared import config, api_server_started
from core.database import cursor, conn, db_lock
from core.api_server import start_api_server

# Import Views for Persistent adding
from cogs.music import MusicControlView
from cogs.utilities import TicketView, TicketControlView, VoiceGeneratorView, PersistentRoleView

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.presences = True

bot = commands.Bot(command_prefix=config.get("prefix", "!"), intents=intents)
bot.remove_command('help')

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
    with db_lock:
        cursor.execute("SELECT guild_id, user_id, role_id FROM timed_roles WHERE expires_at <= ?", (now,))
        expired = cursor.fetchall()
        
    for guild_id, user_id, role_id in expired:
        guild = bot.get_guild(int(guild_id))
        if guild:
            member = guild.get_member(int(user_id))
            role = guild.get_role(int(role_id))
            if member and role:
                try: await member.remove_roles(role)
                except: pass
    
    if expired:
        with db_lock:
            cursor.executemany(
                "DELETE FROM timed_roles WHERE guild_id=? AND user_id=? AND role_id=?",
                expired
            )
            conn.commit()

@tasks.loop(seconds=3)
async def check_gui_tasks():
    with db_lock:
        cursor.execute("SELECT id, action, payload FROM gui_tasks")
        tasks_list = cursor.fetchall()
        for t in tasks_list:
            cursor.execute("DELETE FROM gui_tasks WHERE id=?", (t[0],))
        conn.commit()
    
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

async def setup_hook():
    print("[THONG BAO] Đang tải các Cogs...")
    await bot.load_extension("cogs.music")
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.economy")
    await bot.load_extension("cogs.utilities")
    await bot.load_extension("cogs.social")
    print("[THONG BAO] Đã tải xong Cogs.")

    # Đăng ký các Persistent Views
    bot.add_view(TicketView())
    bot.add_view(TicketControlView())
    bot.add_view(MusicControlView())
    bot.add_view(VoiceGeneratorView())
    
    with db_lock:
        cursor.execute("SELECT message_id, roles_json FROM reaction_panels")
        panels = cursor.fetchall()
    for msg_id, rjson in panels:
        try:
            roles_data = json.loads(rjson)
            bot.add_view(PersistentRoleView(roles_data, f"rr_panel_{msg_id}"))
        except: pass
        
    await bot.tree.sync()

bot.setup_hook = setup_hook

@bot.event
async def on_ready():
    global api_server_started
    print(f'[THONG BAO] Bot {bot.user} da Started thanh cong!')
    
    if not api_server_started:
        bot.loop.create_task(start_api_server(bot))
        from core import shared
        shared.api_server_started = True

    if not check_timed_roles.is_running():
        check_timed_roles.start()
    if not check_gui_tasks.is_running():
        check_gui_tasks.start()
    await export_server_data()
    print("[THONG BAO] Da cap nhat danh sach Role và Channel moi nhat.")

@bot.event
async def on_guild_join(g): await export_server_data()
@bot.event
async def on_guild_remove(g): await export_server_data()
@bot.event
async def on_guild_role_create(r): await export_server_data()
@bot.event
async def on_guild_role_update(b, a): await export_server_data()
@bot.event
async def on_guild_channel_create(c): await export_server_data()
@bot.event
async def on_guild_channel_update(b, a): await export_server_data()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bạn không có quyền thực hiện lệnh này.")
        return
    print(f"[LOI LENH] {error}")

if __name__ == "__main__":
    if not config.get("token"):
        print("❌ Chưa cấu hình Token Bot trong config.json!")
        sys.exit(1)
    
    try:
        bot.run(config["token"])
    except Exception as e:
        print(f"❌ Không thể khởi chạy Bot: {e}")