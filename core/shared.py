import os
import json
import threading
import sys
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

# Đọc đối số dòng lệnh để xác định file config
config_file = "config.json"
for arg in sys.argv:
    if arg.startswith("--config="):
        config_file = arg.split("=")[1]
        break

# Cấu hình
config = {}
try:
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print(f"❌ Lỗi đọc file {config_file}: {e}")

# Nạp đè/bổ sung cấu hình nhạy cảm từ biến môi trường để tăng tính bảo mật
if os.environ.get("DISCORD_TOKEN"):
    config["token"] = os.environ.get("DISCORD_TOKEN")
if os.environ.get("API_SECRET"):
    config["api_secret"] = os.environ.get("API_SECRET")
if os.environ.get("GEMINI_API_KEY"):
    raw_gkey = str(os.environ.get("GEMINI_API_KEY")).strip()
    if (raw_gkey.startswith('"') and raw_gkey.endswith('"')) or (raw_gkey.startswith("'") and raw_gkey.endswith("'")):
        raw_gkey = raw_gkey[1:-1].strip()
    config["gemini_api_key"] = raw_gkey

# Database Lock
db_lock = threading.Lock()

DB_URL = os.environ.get("DATABASE_URL") or config.get("database_url")
USE_PG = DB_URL is not None

# Globals
api_server_started = False
anti_nuke_tracker = {}
temp_voices = set()
level_cooldown = {}
spam_tracker = {}
music_queues = {}
play_history = {}
autoplay_disabled = set()
server_data = {}

API_SECRET = config.get("api_secret", "changeme123")
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': 'True',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    'extractor_args': {
        'youtube': [
            'player_client=ios'
        ]
    }
}
for c_path in ["config/.yt_cookies.data", "config/yt_session.dat", ".cookies.dat", "cookies.txt", "www.youtube.com_cookies.txt"]:
    if os.path.exists(c_path):
        YDL_OPTIONS['cookiefile'] = c_path
        break
import shutil

def get_ffmpeg_executable():
    path = str(config.get("ffmpeg_path", "")).strip()
    
    if path and os.path.exists(path) and (os.name != 'nt' or not path.startswith("/")):
        return path
        
    for p in ["./ffmpeg.exe", "ffmpeg.exe", "./ffmpeg", "ffmpeg"]:
        if os.path.exists(p):
            return p
            
    system_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if system_ffmpeg:
        return system_ffmpeg
        
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
        
    return "./ffmpeg.exe" if os.name == 'nt' else "/usr/bin/ffmpeg"

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
PLATFORM_EMOJI = {"youtube": "▶️", "reddit": "🟧", "tiktok": "🎵", "facebook": "🔵"}

import re
from discord.ext import commands

SCAM_REGEX_GLOBAL = re.compile(r"(discord\.gift\/|steamcommun.*\.com|discorcl\.gift|discordapp\.click|free-nitro|robux-free)", re.IGNORECASE)


def is_mod():
    """Check decorator dùng chung cho tất cả Cog: cho phép Admin hoặc người có Mod role."""
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        guild_id = str(ctx.guild.id)
        server_cfg = config.get("servers", {}).get(guild_id, config)
        mod_role_ids = list(server_cfg.get("mod_role_ids", []))
        old_mod = server_cfg.get("mod_role_id")
        if old_mod and str(old_mod) not in [str(x) for x in mod_role_ids]:
            mod_role_ids.append(old_mod)
        if not mod_role_ids:
            return False
        user_role_ids = [r.id for r in ctx.author.roles]
        return any(int(m) in user_role_ids for m in mod_role_ids)
    return commands.check(predicate)

def update_bot_command_names(bot):
    """Cập nhật tên lệnh & aliases linh hoạt trên bot instance mà không cần restart."""
    if not bot:
        return
    mapping = {
        "play": config.get("cmd_play", "play") or "play",
        "stop": config.get("cmd_stop", "stop") or "stop",
        "skip": config.get("cmd_skip", "skip") or "skip",
        "pause": config.get("cmd_pause", "pause") or "pause",
        "resume": config.get("cmd_resume", "resume") or "resume",
        "ping": config.get("cmd_ping", "ping") or "ping",
        "warn": config.get("cmd_warn", "warn") or "warn",
        "timed_role": config.get("cmd_timed_role", "timed_role") or "timed_role",
        "kick": config.get("cmd_kick", "kick") or "kick",
        "mute": config.get("cmd_mute", "mute") or "mute",
        "ban": config.get("cmd_ban", "ban") or "ban",
        "clear": config.get("cmd_clear", "clear") or "clear",
        "addword": config.get("cmd_addword", "addword") or "addword",
        "delword": config.get("cmd_delword", "delword") or "delword",
        "profile_cmd": config.get("cmd_profile", "profile") or "profile",
        "profile": config.get("cmd_profile", "profile") or "profile",
        "setup_voice": config.get("cmd_setup_voice", "setup_voice") or "setup_voice",
        "ticket_setup": config.get("cmd_ticket_setup", "ticket_setup") or "ticket_setup",
    }
    
    try:
        for cmd in list(bot.commands):
            cb_name = getattr(cmd.callback, "__name__", cmd.name)
            default_key = cb_name.replace("_cmd", "")
            target_name = mapping.get(cb_name) or mapping.get(default_key)
            
            if target_name:
                old_name = cmd.name
                if old_name in bot.all_commands and bot.all_commands[old_name] == cmd:
                    del bot.all_commands[old_name]
                
                cmd.name = target_name
                if default_key != target_name and default_key not in cmd.aliases:
                    cmd.aliases = list(set(list(cmd.aliases) + [default_key]))
                
                bot.all_commands[target_name] = cmd
                for alias in cmd.aliases:
                    bot.all_commands[alias] = cmd
    except Exception as e:
        print(f"[CMD UPDATE ERROR] Không thể cập nhật tên lệnh: {e}")

