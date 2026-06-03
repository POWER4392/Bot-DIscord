import os
import json
import threading
import sys
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
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'False', 'quiet': True, 'no_warnings': True, 'default_search': 'scsearch', 'extractor_args': {'youtube': ['player_client=android_vr']}}
if os.path.exists("cookies.txt"):
    YDL_OPTIONS['cookiefile'] = "cookies.txt"
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
PLATFORM_EMOJI = {"youtube": "▶️", "reddit": "🟧", "tiktok": "🎵", "facebook": "🔵"}

import re
SCAM_REGEX_GLOBAL = re.compile(r"(discord\.gift\/|steamcommun.*\.com|discorcl\.gift|discordapp\.click|free-nitro|robux-free)", re.IGNORECASE)
