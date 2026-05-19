import os
import json
import threading

# Cấu hình
config = {}
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print(f"❌ Lỗi đọc file config.json: {e}")

# Database Lock
db_lock = threading.Lock()

DB_URL = os.environ.get("DATABASE_URL")
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

API_SECRET = config.get("api_secret", "changeme123")
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True, 'default_search': 'ytsearch'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
PLATFORM_EMOJI = {"youtube": "▶️", "reddit": "🟧", "tiktok": "🎵", "facebook": "🔵"}

import re
SCAM_REGEX_GLOBAL = re.compile(r"(discord\.gift\/|steamcommun.*\.com|discorcl\.gift|discordapp\.click|free-nitro|robux-free)", re.IGNORECASE)
