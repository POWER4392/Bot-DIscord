# Đặc tả Giao diện Lập trình API (API Contract Specification)

Tài liệu này định nghĩa chi tiết các API endpoints được cung cấp bởi API Server nội bộ của Bot (`core/api_server.py`) nhằm phục vụ Web Dashboard của Nhóm 69.

---

## 🔒 1. Xác thực (Authentication)

Tất cả các API endpoints đều yêu cầu header xác thực `X-API-Key` để bảo mật thông tin cấu hình bot.

- **Header name:** `X-API-Key`
- **Giá trị:** Khóa bí mật được định nghĩa trong `config.json` hoặc biến môi trường `API_SECRET`.

---

## 📡 2. Các Endpoints Chi Tiết

### 📊 2.1 Lấy Thống kê Trạng thái Bot (Get Bot Stats)
- **Endpoint:** `GET /api/stats`
- **Headers:** `X-API-Key: <secret>`
- **Response (200 OK):**
```json
{
  "status": "online",
  "latency_ms": 45.2,
  "guilds_count": 2,
  "users_count": 1420,
  "uptime_seconds": 86400,
  "cpu_usage_pct": 5.4,
  "memory_usage_mb": 124.5
}
```

---

### 💬 2.2 Cập nhật Cấu hình AI Chatbot (Update AI Config)
- **Endpoint:** `POST /api/config/ai`
- **Headers:**
  - `X-API-Key: <secret>`
  - `Content-Type: application/json`
- **Request Body:**
```json
{
  "gemini_api_key": "AIzaSy...",
  "ai_system_prompt": "Bạn là trợ lý ảo Discord thân thiện...",
  "automod_mute_minutes": 10
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Cấu hình AI đã được cập nhật thành công!"
}
```

---

### 🎭 2.3 Lấy cấu hình Reaction Roles (Get Reaction Roles)
- **Endpoint:** `GET /api/config/reaction-roles`
- **Headers:** `X-API-Key: <secret>`
- **Response (200 OK):**
```json
{
  "rr_channel_id": "1458038155562319875",
  "rr_title": "Bảng đăng ký vai trò",
  "rr_roles_list": [
    {
      "role_id": "708859115396399125",
      "role_name": "Game thủ",
      "emoji": "🎮"
    },
    {
      "role_id": "708859109448876065",
      "role_name": "Lập trình viên",
      "emoji": "💻"
    }
  ]
}
```

---

### ⚙️ 2.4 Cập nhật Cấu hình Reaction Roles (Update Reaction Roles)
- **Endpoint:** `POST /api/config/reaction-roles`
- **Headers:**
  - `X-API-Key: <secret>`
  - `Content-Type: application/json`
- **Request Body:**
```json
{
  "rr_channel_id": "1458038155562319875",
  "rr_title": "Bảng chọn vai trò thành viên",
  "rr_roles_list": [
    "708859115396399125",
    "708859109448876065"
  ]
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Cấu hình Reaction Roles đã được đồng bộ!"
}
```
