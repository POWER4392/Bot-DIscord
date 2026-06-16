# Dac ta Giao dien Lap trinh API (API Contract Specification)

Tai lieu nay dinh nghia chi tiet cac API endpoints duoc cung cap boi API Server noi bo cua Bot (`core/api_server.py`) nham phuc vu Web Dashboard.

---

## 1. Xac thuc (Authentication)

Tat ca cac API endpoints deu yeu cau header xac thuc `X-API-Key` de bao mat thong tin cau hinh bot.

- **Header name:** `X-API-Key`
- **Gia tri:** Khoa bi mat duoc dinh nghia trong `config.json` (`api_secret`) hoac bien moi truong `API_SECRET`.

---

## 2. Endpoint chinh

Tat ca cac action deu gui qua **mot endpoint duy nhat**:

```
POST /api
Content-Type: application/json
X-API-Key: <secret>

{ "action": "<ACTION_NAME>", ... }
```

---

## 2.1 Thong ke Co ban — GET_DASHBOARD_STATS

```json
// Request
{ "action": "GET_DASHBOARD_STATS" }

// Response
{
  "ok": true, "bot_status": "Online",
  "total_servers": 2, "total_users": 1420,
  "ping_ms": 45, "loaded_cogs": ["Music", "Moderation"],
  "active_voice_channels": 3
}
```

---

## 2.2 Thong ke Nang cao — GET_BOT_METRICS (Issue #32)

```json
// Request
{ "action": "GET_BOT_METRICS" }

// Response
{
  "ok": true, "guilds": 2, "total_members": 1420,
  "voice_connections": 3, "latency_ms": 45,
  "loaded_cogs": ["Music", "AIChatbot"],
  "ai_active_sessions": 5,
  "ai_model": "gemini-1.5-flash",
  "ai_api_configured": true,
  "db_users": 100, "db_warnings": 12, "db_ai_messages": 340
}
```

---

## 2.3 Trang thai AI — GET_AI_STATUS

```json
{ "action": "GET_AI_STATUS" }
// Response
{
  "ok": true,
  "gemini_api_configured": true,
  "ai_channel_id": "122333444555666",
  "ai_system_prompt": "Ban la tro ly ao..."
}
```

## 2.4 Cau hinh AI — SET_AI_CONFIG (Owner key)

```json
{
  "action": "SET_AI_CONFIG",
  "payload": {
    "ai_channel_id": "122333444555666",
    "ai_system_prompt": "Ban la tro ly ao Discord than thien."
  }
}
```

---

## 2.5 Lich su hoi thoai AI — GET_CHAT_HISTORY (Issue #32)

```json
// Request
{ "action": "GET_CHAT_HISTORY", "guild_id": "111222333", "user_id": "444555", "limit": 50 }

// Response
{
  "ok": true,
  "history": [
    { "user_id": "444555", "role": "user", "content": "Xin chao!", "timestamp": 1718000000.0 },
    { "user_id": "444555", "role": "model", "content": "Chao ban!", "timestamp": 1718000005.0 }
  ],
  "count": 2
}
```

## 2.6 Xoa lich su AI — CLEAR_CHAT_HISTORY (Issue #32, Owner key)

```json
// Xoa 1 user
{ "action": "CLEAR_CHAT_HISTORY", "guild_id": "111222333", "user_id": "444555" }
// Xoa ca guild
{ "action": "CLEAR_CHAT_HISTORY", "guild_id": "111222333" }
// Response: { "ok": true, "deleted": 42 }
```

---

## 2.7 Quan ly Blacklist — LIST / ADD / REMOVE (Issue #32)

```json
// Lay danh sach tu cam
{ "action": "LIST_BLACKLIST", "guild_id": "111222333" }
// -> { "ok": true, "words": ["badword1", "badword2"], "count": 2 }

// Them tu cam (Owner key)
{ "action": "ADD_BLACKLIST", "guild_id": "111222333", "word": "badword" }

// Xoa tu cam (Owner key)
{ "action": "REMOVE_BLACKLIST", "guild_id": "111222333", "word": "badword" }
```

---

## 2.8 Reaction Roles — SPAWN_RR_PANEL

```json
{
  "action": "SPAWN_RR_PANEL",
  "payload": {
    "guild_id": "111222333",
    "channel_id": "122333444555666",
    "title": "Chon vai tro",
    "desc": "Nhan nut de chon role",
    "footer": "Ho tro: @Admin",
    "roles": [{ "name": "Gamer", "desc": "Nhan thong bao game" }]
  }
}
```

---

## 2.9 Cau hinh he thong — GET_CONFIG / UPDATE_CONFIG (Owner key)

```json
{ "action": "GET_CONFIG" }
{ "action": "UPDATE_CONFIG", "payload": { "prefix": "!", "api_port": 8080 } }
```

---

## 3. Health Check Endpoint

```
GET /health
```
Tra ve JSON trang thai bot (khong yeu cau API Key). Dung cho Render Cloud uptime monitoring.

```json
{
  "status": "ok", "bot_online": true,
  "guilds": 2, "latency_ms": 45,
  "uptime": "02h 14m 37s",
  "database": "postgresql", "environment": "production"
}
```

---

## 4. Bao mat & Gioi han

| Tinh nang | Chi tiet |
|-----------|----------|
| Rate Limiting | Toi da 30 request/phut/IP tren /api |
| CORS | Cho phep * (ho tro Dashboard tu moi origin) |
| Payload limit | Toi da 64 KB moi request |
| Auth | Header X-API-Key bat buoc; mot so action chi Owner key |

---

*Tai lieu cap nhat theo Issue #32 - Tuan 4.1 (Backend: Tran Duc Manh)*
