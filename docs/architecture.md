# Kiến trúc Hệ thống (System Architecture Specification)

Tài liệu này thuyết minh kiến trúc và cách thức hoạt động của hệ thống Discord Bot quản lý tích hợp AI của Nhóm 69.

---

## 🏗️ 1. Sơ đồ Khối Tổng Quan (High-Level Architecture)

Hệ thống được thiết kế theo mô hình **All-In-One** tách biệt giữa phần xử lý nghiệp vụ Bot (Core Discord Service) và phần giao diện quản lý (Web Dashboard). hai thành phần này giao tiếp với nhau thông qua giao thức HTTP REST API nội bộ.

```
+-----------------------------------+
|          Web Dashboard            |  <-- Giao diện quản trị (HTML/CSS/JS)
|       (Triển khai Render)         |
+-----------------------------------+
                  |
                  |  HTTP Requests (kèm X-API-Key)
                  v
+-----------------------------------+
|         API Server Engine         |  <-- REST API Handler (core/api_server.py)
|         (Port 8081 nội bộ)        |
+-----------------------------------+
                  |
                  |  Lọc Dữ liệu & Gọi Cấu hình
                  v
+-----------------------------------+
|       Discord Bot Service         |  <-- Lập trình bất đồng bộ (discord.py)
|         (Chạy Main Core)          |
+-----------------------------------+
       /          |          \
      /           |           \
     v            v            v
+--------+   +---------+   +-------+
|  Cogs  |   | Database|   |Gemini |  <-- AI Chatbot Integration
| Modules|   | SQLite/ |   |  API  |      (Google AI Studio SDK)
+--------+   | Postgres|   +-------+
             +---------+
```

---

## ⚙️ 2. Các Thành Phần Chính (Key Components)

### 1. Web Dashboard (Frontend)
- Một ứng dụng Web tĩnh (HTML5, Vanilla CSS, Vanilla JavaScript) sử dụng hiệu ứng **Glassmorphism**.
- Kết nối tới API Server để hiển thị biểu đồ thống kê thời gian thực của máy chủ (Uptime, số thành viên, CPU, RAM) và thực hiện cấu hình trực quan cho Bot.

### 2. API Server Engine (Middleware)
- Được khởi chạy như một luồng nền bất đồng bộ (`asyncio`) ngay khi Bot khởi động.
- Lắng nghe các yêu cầu PATCH/POST/GET từ dashboard để thay đổi cấu hình hệ thống thời gian thực mà không cần khởi động lại Bot.

### 3. Discord Bot Core (Backend)
- Xây dựng dựa trên thư viện `discord.py` phiên bản mới nhất.
- Hỗ trợ cơ chế **Cogs (Plugin-based Architecture)** để chia nhỏ các module chức năng như:
  - `Moderation`: Xử lý vi phạm, cảnh báo, kick, ban.
  - `Music`: Phát nhạc từ các nền tảng trực tuyến.
  - `Welcome`: Tự động gửi ảnh chào mừng thành viên mới và kích hoạt kiểm tra xác minh.

### 4. Database Layer (Storage)
- Sử dụng interface trừu tượng (`core/database.py`) cho phép chuyển đổi mượt mà giữa **SQLite** (dùng cho môi trường chạy thử cục bộ) và **Neon Serverless PostgreSQL** (dùng khi deploy lên Render Cloud).
