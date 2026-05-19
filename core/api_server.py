import json
from aiohttp import web
from core.shared import config, API_SECRET
from core.database import cursor, conn, db_lock
import os

def create_handle_api(bot):
    async def handle_api(request: web.Request):
        auth = request.headers.get("X-API-Key", "")
        if auth != API_SECRET:
            return web.json_response({"ok": False, "error": "Unauthorized"}, status=401)
        
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"ok": False, "error": "Invalid JSON"}, status=400)
        
        action = data.get("action", "")
        
        if action == "SPAWN_RR_PANEL":
            with db_lock:
                cursor.execute(
                    "INSERT INTO gui_tasks (action, payload) VALUES (?, ?)",
                    ("SPAWN_RR_PANEL", json.dumps(data.get("payload", {})))
                )
                conn.commit()
            return web.json_response({"ok": True, "msg": "Task queued"})
        
        elif action == "RELOAD_CONFIG":
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    new_config = json.load(f)
                    config.clear()
                    config.update(new_config)
                return web.json_response({"ok": True, "msg": "Config reloaded"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})
        
        elif action == "STATUS":
            return web.json_response({
                "ok": True,
                "bot": str(bot.user),
                "guilds": len(bot.guilds),
                "latency_ms": round(bot.latency * 1000)
            })
            
        elif action == "DB_QUERY":
            query = data.get("query", "")
            params = data.get("params", [])
            try:
                with db_lock:
                    cursor.execute(query, params)
                    if query.strip().upper().startswith("SELECT"):
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        rows = cursor.fetchall()
                        results = [dict(zip(columns, row)) for row in rows]
                        return web.json_response({"ok": True, "data": results})
                    else:
                        conn.commit()
                        return web.json_response({"ok": True, "rows_affected": cursor.rowcount})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})
        
        return web.json_response({"ok": False, "error": "Unknown action"}, status=400)
    return handle_api

async def handle_health(request: web.Request):
    return web.Response(text="Discord Bot is Online 🟢")

async def start_api_server(bot):
    app = web.Application()
    app.router.add_post("/api", create_handle_api(bot))
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", config.get("api_port", 8080)))
    site = web.TCPSite(runner, "0.0.0.0", port)
    try:
        await site.start()
        print(f"[API] HTTP API server đang lắng nghe tại cổng {port}")
    except OSError as e:
        if e.errno == 10048:
            print(f"❌ [API Error] Không thể mở cổng {port} vì đã bị chiếm dụng.")
        else:
            print(f"❌ [API Error] Lỗi khi khởi động server: {e}")
