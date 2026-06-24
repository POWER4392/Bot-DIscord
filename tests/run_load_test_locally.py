import subprocess
import time
import sys
import os

def main():
    python_exe = sys.executable
    print(f"Using Python interpreter: {python_exe}")

    server_code = """
import asyncio
from aiohttp import web
from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.abspath('.'))
from core.api_server import start_api_server

# Mock bot
bot = MagicMock()
bot.user = "LoadTestBot#9999"
bot.guilds = []
bot.latency = 0.05
bot.cogs = {}
loop = asyncio.new_event_loop()
bot.loop = loop

# Override config api_port
from core.shared import config
config["api_port"] = 8085

async def run():
    await start_api_server(bot)
    while True:
        await asyncio.sleep(3600)

try:
    loop.run_until_complete(run())
except KeyboardInterrupt:
    pass
"""

    # Save temporary server script
    with open("temp_server.py", "w", encoding="utf-8") as f:
        f.write(server_code)

    print("[Info] Starting temporary mock API server on port 8085...")
    server_env = os.environ.copy()
    server_env["PYTHONIOENCODING"] = "utf-8"
    server_process = subprocess.Popen([python_exe, "temp_server.py"], env=server_env)
    time.sleep(2.0)  # Wait for server to start

    try:
        print("[Info] Running load test...")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["TARGET_URL"] = "http://127.0.0.1:8085/api"
        env["TOTAL_REQUESTS"] = "50"
        env["CONCURRENCY"] = "5"
        subprocess.run([python_exe, "tests/load_test.py"], env=env, check=True)
    except Exception as e:
        print(f"[Error] during load test: {e}")
    finally:
        print("[Info] Shutting down mock API server...")
        server_process.terminate()
        server_process.wait()
        if os.path.exists("temp_server.py"):
            os.remove("temp_server.py")
        print("[Info] Done!")

if __name__ == "__main__":
    main()
