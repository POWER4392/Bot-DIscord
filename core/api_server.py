import json
from aiohttp import web
from core.shared import config, API_SECRET
from core.database import cursor, conn, db_lock
import os

def create_handle_api(bot):
    async def handle_api(request: web.Request):
        auth = request.headers.get("X-API-Key", "")
        from core.shared import config_file
        allowed_keys = config.get("api_secrets", [])
        if not isinstance(allowed_keys, list):
            allowed_keys = [allowed_keys]
        if API_SECRET not in allowed_keys:
            allowed_keys.append(API_SECRET)
            
        if auth not in allowed_keys:
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
        
        elif action == "GET_CONFIG":
            return web.json_response({"ok": True, "data": config})
            
        elif action == "UPDATE_CONFIG":
            if auth != API_SECRET:
                return web.json_response({
                    "ok": False, 
                    "error": "Bạn không có quyền thay đổi cấu hình hệ thống (Chỉ Owner sở hữu Key chính mới có quyền này)."
                }, status=403)
            try:
                new_config = data.get("payload", {})
                if not new_config:
                    return web.json_response({"ok": False, "error": "Empty payload"})
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(new_config, f, indent=4, ensure_ascii=False)
                config.clear()
                config.update(new_config)
                return web.json_response({"ok": True, "msg": "Config updated"})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})
                
        elif action == "GET_SERVER_DATA":
            import core.shared as shared
            return web.json_response({"ok": True, "data": shared.server_data})
        
        elif action == "GET_DASHBOARD_STATS":
            import core.shared as shared
            # Tra ve cac so lieu phuc vu dashboard admin chi tiet
            return web.json_response({
                "ok": True,
                "bot_status": "Online",
                "total_servers": len(bot.guilds),
                "ping_ms": round(bot.latency * 1000) if bot.latency else 0,
                "loaded_cogs": list(bot.cogs.keys()),
                "total_users": sum(len(g.members) for g in bot.guilds),
                "active_voice_channels": len(bot.voice_clients)
            })
            
        elif action == "GET_AI_STATUS":
            gemini_key = os.environ.get("GEMINI_API_KEY", "")
            return web.json_response({
                "ok": True,
                "gemini_api_configured": gemini_key != "",
                "ai_channel_id": config.get("ai_channel_id", ""),
                "ai_system_prompt": config.get("ai_system_prompt", "Bạn là một trợ lý ảo Discord thân thiện.")
            })
            
        elif action == "SET_AI_CONFIG":
            from core.shared import config_file
            if auth != API_SECRET:
                return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
            try:
                payload = data.get("payload", {})
                config["ai_channel_id"] = payload.get("ai_channel_id", config.get("ai_channel_id", ""))
                config["ai_system_prompt"] = payload.get("ai_system_prompt", config.get("ai_system_prompt", ""))
                
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                return web.json_response({"ok": True, "msg": "Cấu hình AI đã được cập nhật thành công."})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})

        elif action == "GET_AI_CHANNELS":
            # Tra ve danh sach cac text channel de lua chon lam kenh AI Chat
            channels = []
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    channels.append({
                        "guild_id": str(guild.id),
                        "guild_name": guild.name,
                        "channel_id": str(channel.id),
                        "channel_name": channel.name
                    })
            return web.json_response({"ok": True, "channels": channels})
            
        elif action == "STATUS":
            return web.json_response({
                "ok": True,
                "bot": str(bot.user),
                "guilds": len(bot.guilds),
                "latency_ms": round(bot.latency * 1000) if bot.latency is not None else 0
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
