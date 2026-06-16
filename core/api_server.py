import json
import time
from collections import defaultdict
from aiohttp import web
from core.shared import config, API_SECRET
from core.database import cursor, conn, db_lock
import os

# ---------------------------------------------------------------------------
# Rate Limiting (Fix #34 - Viet QA/Security)
# Simple in-memory rate limiter: max 30 requests/minute per IP
# ---------------------------------------------------------------------------
_rate_limit_store = defaultdict(list)
RATE_LIMIT_MAX = 30
RATE_LIMIT_WINDOW = 60  # seconds


def check_rate_limit(client_ip: str) -> bool:
    """Returns True if request is allowed, False if rate-limited."""
    now = time.time()
    timestamps = _rate_limit_store[client_ip]
    # Slide window: remove timestamps older than window
    _rate_limit_store[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[client_ip].append(now)
    return True


# ---------------------------------------------------------------------------
# CORS Middleware (Fix #34 - Viet QA/Security)
# Allows Web Dashboard running in browser to call the API
# ---------------------------------------------------------------------------
@web.middleware
async def cors_middleware(request: web.Request, handler):
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return web.Response(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-API-Key",
                "Access-Control-Max-Age": "86400",
            }
        )
    response = await handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    return response


@web.middleware
async def rate_limit_middleware(request: web.Request, handler):
    # Only rate-limit the /api endpoint
    if request.path == "/api":
        client_ip = request.remote or "unknown"
        if not check_rate_limit(client_ip):
            return web.json_response(
                {"ok": False, "error": "Quá nhiều yêu cầu. Vui lòng thử lại sau 60 giây."},
                status=429,
                headers={"Retry-After": "60"}
            )
    return await handler(request)


# ---------------------------------------------------------------------------
# Health Check Endpoint (Fix #33 - Long DevOps)
# Returns structured JSON for Render Cloud health monitoring
# ---------------------------------------------------------------------------
_bot_start_time = time.time()


async def handle_health(request: web.Request):
    """
    GET /health — JSON health check for Render Cloud uptime monitoring.
    Returns bot status, uptime, ping, loaded modules.
    """
    bot = request.app["bot"]
    uptime_seconds = int(time.time() - _bot_start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return web.json_response({
        "status": "ok",
        "bot_online": bot.is_ready(),
        "bot_user": str(bot.user) if bot.user else None,
        "guilds": len(bot.guilds),
        "latency_ms": round(bot.latency * 1000) if bot.latency else 0,
        "uptime": f"{hours:02d}h {minutes:02d}m {seconds:02d}s",
        "uptime_seconds": uptime_seconds,
        "loaded_cogs": list(bot.cogs.keys()),
        "database": "postgresql" if os.environ.get("DATABASE_URL") else "sqlite",
        "environment": "production" if os.environ.get("RENDER") else "development"
    })


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

        # Security: limit payload size (prevent abuse)
        raw_body = await request.read()
        if len(raw_body) > 64 * 1024:  # 64 KB max
            return web.json_response({"ok": False, "error": "Payload quá lớn (>64KB)."}, status=413)

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

        # ---------------------------------------------------------------
        # Issue #32 — New Backend API Endpoints for Web Dashboard
        # ---------------------------------------------------------------

        elif action == "GET_CHAT_HISTORY":
            """Lấy lịch sử hội thoại AI theo guild (và tùy chọn theo user)."""
            guild_id = data.get("guild_id", "")
            user_id = data.get("user_id", None)
            limit = min(int(data.get("limit", 50)), 200)
            try:
                with db_lock:
                    if user_id:
                        cursor.execute(
                            "SELECT user_id, role, content, timestamp FROM ai_conversations "
                            "WHERE guild_id=? AND user_id=? ORDER BY timestamp DESC LIMIT ?",
                            (str(guild_id), str(user_id), limit)
                        )
                    else:
                        cursor.execute(
                            "SELECT user_id, role, content, timestamp FROM ai_conversations "
                            "WHERE guild_id=? ORDER BY timestamp DESC LIMIT ?",
                            (str(guild_id), limit)
                        )
                    rows = cursor.fetchall()
                history = [
                    {"user_id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]}
                    for r in rows
                ]
                return web.json_response({"ok": True, "history": history, "count": len(history)})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})

        elif action == "CLEAR_CHAT_HISTORY":
            """Xóa lịch sử hội thoại AI theo guild hoặc user cụ thể."""
            if auth != API_SECRET:
                return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
            guild_id = data.get("guild_id", "")
            user_id = data.get("user_id", None)
            try:
                with db_lock:
                    if user_id:
                        cursor.execute(
                            "DELETE FROM ai_conversations WHERE guild_id=? AND user_id=?",
                            (str(guild_id), str(user_id))
                        )
                    else:
                        cursor.execute(
                            "DELETE FROM ai_conversations WHERE guild_id=?",
                            (str(guild_id),)
                        )
                    conn.commit()
                    deleted = cursor.rowcount
                # Also clear in-memory sessions in AIChatbot cog
                ai_cog = bot.cogs.get("AIChatbot")
                if ai_cog:
                    if user_id:
                        ai_cog.chat_sessions.pop((int(guild_id), int(user_id)), None)
                    else:
                        keys = [k for k in ai_cog.chat_sessions if str(k[0]) == str(guild_id)]
                        for k in keys:
                            del ai_cog.chat_sessions[k]
                return web.json_response({"ok": True, "deleted": deleted})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})

        elif action == "GET_BOT_METRICS":
            """Thống kê nâng cao: tổng messages, AI sessions, bảng DB."""
            try:
                metrics = {
                    "ok": True,
                    "guilds": len(bot.guilds),
                    "total_members": sum(g.member_count or 0 for g in bot.guilds),
                    "voice_connections": len(bot.voice_clients),
                    "latency_ms": round(bot.latency * 1000) if bot.latency else 0,
                    "loaded_cogs": list(bot.cogs.keys()),
                }
                # AI session stats
                ai_cog = bot.cogs.get("AIChatbot")
                metrics["ai_active_sessions"] = len(ai_cog.chat_sessions) if ai_cog else 0
                metrics["ai_model"] = ai_cog.model_name if ai_cog else "N/A"
                metrics["ai_api_configured"] = bool(os.environ.get("GEMINI_API_KEY"))
                # DB counts
                with db_lock:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    metrics["db_users"] = (cursor.fetchone() or [0])[0]
                    cursor.execute("SELECT COUNT(*) FROM warnings")
                    metrics["db_warnings"] = (cursor.fetchone() or [0])[0]
                    cursor.execute("SELECT COUNT(*) FROM ai_conversations")
                    metrics["db_ai_messages"] = (cursor.fetchone() or [0])[0]
                    
                    # Thống kê token sử dụng (Issue #35 - Duy AI/ML)
                    cursor.execute("SELECT SUM(prompt_tokens), SUM(completion_tokens), SUM(total_tokens) FROM ai_token_usage")
                    token_row = cursor.fetchone()
                    metrics["ai_total_prompt_tokens"] = token_row[0] or 0 if token_row else 0
                    metrics["ai_total_completion_tokens"] = token_row[1] or 0 if token_row else 0
                    metrics["ai_total_tokens"] = token_row[2] or 0 if token_row else 0
                return web.json_response(metrics)
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})

        elif action == "LIST_BLACKLIST":
            """Lấy danh sách từ cấm theo guild."""
            guild_id = data.get("guild_id", "")
            if not guild_id:
                return web.json_response({"ok": False, "error": "Thiếu guild_id"})
            try:
                with db_lock:
                    cursor.execute(
                        "SELECT word FROM blacklists WHERE guild_id=? ORDER BY word ASC",
                        (str(guild_id),)
                    )
                    words = [r[0] for r in cursor.fetchall()]
                return web.json_response({"ok": True, "guild_id": guild_id, "words": words, "count": len(words)})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})

        elif action == "ADD_BLACKLIST":
            """Thêm từ vào danh sách cấm."""
            if auth != API_SECRET:
                return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
            guild_id = data.get("guild_id", "")
            word = data.get("word", "").strip().lower()
            if not guild_id or not word:
                return web.json_response({"ok": False, "error": "Thiếu guild_id hoặc word"})
            try:
                with db_lock:
                    cursor.execute(
                        "INSERT OR IGNORE INTO blacklists (guild_id, word) VALUES (?, ?)",
                        (str(guild_id), word)
                    )
                    conn.commit()
                return web.json_response({"ok": True, "msg": f"'{word}' đã được thêm vào blacklist."})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})

        elif action == "REMOVE_BLACKLIST":
            """Xóa từ khỏi danh sách cấm."""
            if auth != API_SECRET:
                return web.json_response({"ok": False, "error": "Unauthorized"}, status=403)
            guild_id = data.get("guild_id", "")
            word = data.get("word", "").strip().lower()
            if not guild_id or not word:
                return web.json_response({"ok": False, "error": "Thiếu guild_id hoặc word"})
            try:
                with db_lock:
                    cursor.execute(
                        "DELETE FROM blacklists WHERE guild_id=? AND word=?",
                        (str(guild_id), word)
                    )
                    conn.commit()
                    deleted = cursor.rowcount
                if deleted:
                    return web.json_response({"ok": True, "msg": f"'{word}' đã được xóa khỏi blacklist."})
                else:
                    return web.json_response({"ok": False, "error": f"'{word}' không có trong blacklist."})
            except Exception as e:
                return web.json_response({"ok": False, "error": str(e)})

        return web.json_response({"ok": False, "error": "Unknown action"}, status=400)
    return handle_api


async def start_api_server(bot):
    app = web.Application(middlewares=[cors_middleware, rate_limit_middleware])
    app["bot"] = bot  # Store bot reference for health endpoint
    app.router.add_post("/api", create_handle_api(bot))
    app.router.add_options("/api", lambda r: web.Response(status=200))  # CORS preflight
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_health)  # Root also returns health info

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", config.get("api_port", 8080)))
    site = web.TCPSite(runner, "0.0.0.0", port)
    try:
        await site.start()
        print(f"[API] HTTP API server đang lắng nghe tại cổng {port}")
        print(f"[API] Health check: http://0.0.0.0:{port}/health")
    except OSError as e:
        if e.errno == 10048:
            print(f"❌ [API Error] Không thể mở cổng {port} vì đã bị chiếm dụng.")
        else:
            print(f"❌ [API Error] Lỗi khi khởi động server: {e}")
