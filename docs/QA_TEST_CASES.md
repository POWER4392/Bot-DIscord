# 📋 Tài Liệu Kiểm Thử QA/QC — Discord Bot

> **Người thực hiện:** Viet (QA/QC Engineer)  
> **Phiên bản:** v3.2.0 (Gemini Edition)  
> **Ngày cập nhật:** 2026-06-10  
> **Phạm vi:** API Server, AI Chatbot, Web Dashboard, Security

---

## I. API Server Endpoints

### TC-API-01: Health Check Endpoint

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-01 |
| **Mô tả** | Kiểm tra endpoint `/health` trả về JSON hợp lệ |
| **Điều kiện** | Bot đang chạy, API server online |
| **Bước thực hiện** | `curl http://localhost:8080/health` |
| **Kết quả mong đợi** | HTTP 200, body có `"status": "ok"`, `"bot_online": true` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-02: Xác thực API Key hợp lệ

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-02 |
| **Mô tả** | Gọi `/api` với API Key đúng |
| **Bước thực hiện** | POST `/api` với header `X-API-Key: changeme123`, body `{"action":"STATUS"}` |
| **Kết quả mong đợi** | HTTP 200, `"ok": true`, có `"bot"` field |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-03: Từ chối API Key sai

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-03 |
| **Mô tả** | Gọi `/api` với API Key sai |
| **Bước thực hiện** | POST `/api` với header `X-API-Key: wrongkey`, body `{"action":"STATUS"}` |
| **Kết quả mong đợi** | HTTP 401, `"error": "Unauthorized"` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-04: Rate Limiting (Bảo vệ DDoS)

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-04 |
| **Mô tả** | Gửi > 30 request trong 60 giây từ cùng IP |
| **Bước thực hiện** | Loop 35 lần gọi POST `/api` liên tiếp |
| **Kết quả mong đợi** | Request thứ 31 trả về HTTP 429, body `{"error": "Rate limit exceeded"}` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-05: CORS Header

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-05 |
| **Mô tả** | Kiểm tra CORS header có trong response |
| **Bước thực hiện** | Gửi OPTIONS request: `curl -X OPTIONS http://localhost:8080/api` |
| **Kết quả mong đợi** | Response có `Access-Control-Allow-Origin: *` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-06: Payload Size Limit

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-06 |
| **Mô tả** | Gửi payload > 64KB vào `/api` |
| **Bước thực hiện** | POST với body chứa string > 65536 bytes |
| **Kết quả mong đợi** | HTTP 413, `"error": "Payload quá lớn"` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-07: Lấy Dashboard Stats

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-07 |
| **Mô tả** | Lấy thống kê tổng quan dashboard |
| **Bước thực hiện** | POST `{"action": "GET_DASHBOARD_STATS"}` |
| **Kết quả mong đợi** | Response có `total_servers`, `ping_ms`, `loaded_cogs`, `total_users`, `active_voice_channels` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-08: Lấy cấu hình AI

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-08 |
| **Mô tả** | Lấy trạng thái AI chatbot |
| **Bước thực hiện** | POST `{"action": "GET_AI_STATUS"}` |
| **Kết quả mong đợi** | Response có `gemini_api_configured`, `ai_channel_id`, `ai_system_prompt` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-09: Cập nhật cấu hình AI (Owner only)

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-09 |
| **Mô tả** | Gửi `SET_AI_CONFIG` với key phụ (non-owner key) |
| **Bước thực hiện** | Dùng key phụ trong `api_secrets[]`, gọi `SET_AI_CONFIG` |
| **Kết quả mong đợi** | HTTP 403, bị từ chối |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-10: Invalid JSON Body

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-10 |
| **Mô tả** | Gửi body không phải JSON hợp lệ |
| **Bước thực hiện** | POST body = `"not a json"` |
| **Kết quả mong đợi** | HTTP 400, `{"error": "Invalid JSON"}` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-11: Phát hiện lỗi SQLite subquery LIMIT (Tìm thấy và đã fix)

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-11 |
| **Mô tả** | Kiểm tra lưu lịch sử hội thoại AI khi > MAX_HISTORY records |
| **Bước thực hiện** | Gửi 45 tin nhắn liên tiếp vào AI channel (MAX = 40) |
| **Kết quả mong đợi** | Chỉ giữ 40 bản ghi mới nhất, bot không crash |
| **Kết quả thực tế** | ❌ FAIL (lần đầu) — SQLite không hỗ trợ LIMIT trong subquery DELETE |
| **Root cause** | `DELETE ... WHERE id NOT IN (SELECT id ... LIMIT ?)` không hợp lệ trong SQLite |
| **Fix** | Tách thành 2 query: SELECT lấy keep_ids, sau đó DELETE NOT IN (keep_ids) |
| **Kết quả sau fix** | ✅ PASS after fix (commit `cde9774`) |

---

### TC-API-12: GET_CHAT_HISTORY — Lịch sử hội thoại AI

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-12 |
| **Mô tả** | Lấy lịch sử hội thoại AI theo guild |
| **Bước thực hiện** | POST `{"action": "GET_CHAT_HISTORY", "guild_id": "123", "limit": 10}` |
| **Kết quả mong đợi** | `{"ok": true, "history": [...], "count": N}` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-13: LIST_BLACKLIST — Danh sách từ cấm

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-13 |
| **Mô tả** | Lấy danh sách từ cấm theo guild |
| **Bước thực hiện** | POST `{"action": "LIST_BLACKLIST", "guild_id": "123"}` |
| **Kết quả mong đợi** | `{"ok": true, "words": [...], "count": N}` |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-API-14: ADD_BLACKLIST không có Owner Key

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-API-14 |
| **Mô tả** | Gửi ADD_BLACKLIST với key không phải owner |
| **Bước thực hiện** | Dùng key phụ gọi `{"action": "ADD_BLACKLIST", "guild_id": "123", "word": "test"}` |
| **Kết quả mong đợi** | HTTP 403, `{"error": "Unauthorized"}` |
| **Kết quả thực tế** | ✅ PASS |

---

## II. AI Chatbot (cogs/ai_chatbot.py)

### TC-BOT-01: Phản hồi khi được @mention

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-BOT-01 |
| **Mô tả** | Bot phản hồi khi được mention trong bất kỳ kênh nào |
| **Bước thực hiện** | Nhắn `@BotName xin chào!` trong Discord |
| **Kết quả mong đợi** | Bot reply bằng tiếng Việt thân thiện |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-BOT-02: Phản hồi tự động trong AI Channel

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-BOT-02 |
| **Mô tả** | Bot tự trả lời mọi tin nhắn trong kênh AI được cấu hình |
| **Điều kiện** | `ai_channel_id` đã được set trong config |
| **Bước thực hiện** | Nhắn bất kỳ nội dung trong kênh AI |
| **Kết quả mong đợi** | Bot reply trong vòng 5 giây |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-BOT-03: Anti-Spam Rate Limiter — Sliding Window

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-BOT-03 |
| **Mô tả** | Gửi > 5 tin nhắn trong 5 giây từ 1 user |
| **Bước thực hiện** | Nhắn nhanh 6 tin liên tiếp vào kênh AI |
| **Kết quả mong đợi** | Bot cảnh báo spam, không trả lời thêm |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-BOT-04: Anti-Spam Duplicate Detection

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-BOT-04 |
| **Mô tả** | Gửi cùng 1 nội dung 3+ lần liên tiếp |
| **Bước thực hiện** | Gửi `"hello"` 3 lần liên tiếp |
| **Kết quả mong đợi** | Sau lần 3, bot cảnh báo duplicate spam |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-BOT-05: Xử lý tin nhắn rỗng sau mention

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-BOT-05 |
| **Mô tả** | Mention bot không kèm nội dung |
| **Bước thực hiện** | Nhắn `@BotName` (không có text sau) |
| **Kết quả mong đợi** | Bot hướng dẫn cách sử dụng, không crash |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-BOT-06: Xử lý khi không có GEMINI_API_KEY

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-BOT-06 |
| **Mô tả** | Bot hoạt động khi thiếu API key AI |
| **Điều kiện** | `GEMINI_API_KEY` không được đặt |
| **Bước thực hiện** | Mention bot hoặc nhắn trong AI channel |
| **Kết quả mong đợi** | Bot thông báo thiếu API key, không crash |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-BOT-07: Cắt bớt phản hồi > 2000 ký tự

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-BOT-07 |
| **Mô tả** | AI trả về response rất dài |
| **Bước thực hiện** | Hỏi câu hỏi yêu cầu câu trả lời dài (ví dụ: "Viết bài luận 5000 chữ") |
| **Kết quả mong đợi** | Discord message không vượt quá 2000 ký tự, có dấu `...` cuối |
| **Kết quả thực tế** | ✅ PASS |

---

## III. Web Dashboard

### TC-UI-01: Kết nối API thành công

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-UI-01 |
| **Mô tả** | Dashboard kết nối tới Bot API và hiển thị data thực |
| **Bước thực hiện** | Nhập URL và API Key đúng, nhấn nút Kết nối |
| **Kết quả mong đợi** | Stats hiển thị đúng, status "Kết nối thành công" |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-UI-02: Chế độ Demo khi không có API

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-UI-02 |
| **Mô tả** | Dashboard fallback về mock data khi không kết nối được API |
| **Bước thực hiện** | Nhập URL sai hoặc để trống |
| **Kết quả mong đợi** | Toast error hiện ra, dashboard tự chuyển sang "Chế độ Demo" |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-UI-03: Lưu cấu hình AI (Demo Mode)

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-UI-03 |
| **Mô tả** | Lưu system prompt trong Demo Mode |
| **Bước thực hiện** | Tab AI Config → chỉnh system prompt → nhấn Lưu |
| **Kết quả mong đợi** | Toast success, không crash |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-UI-04: Reaction Role Builder — Thêm role

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-UI-04 |
| **Mô tả** | Thêm role vào Reaction Role Builder |
| **Bước thực hiện** | Tab Reaction Roles → nhấn "Thêm Role" |
| **Kết quả mong đợi** | Row mới xuất hiện với input fields |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-UI-05: Reaction Role Builder — Giới hạn 5 role

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-UI-05 |
| **Mô tả** | Không được thêm quá 5 role vào một bảng |
| **Bước thực hiện** | Click "Thêm Role" 6 lần |
| **Kết quả mong đợi** | Lần click thứ 6 hiện toast error giới hạn 5 |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-UI-06: Tab Kiểm Thử & Bảo Mật — Security Audit

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-UI-06 |
| **Mô tả** | Chạy security audit từ dashboard |
| **Bước thực hiện** | Vào tab "Kiểm Thử & Bảo Mật" → nhấn "Chạy Kiểm Thử" |
| **Kết quả mong đợi** | Checklist hiển thị kết quả PASS/FAIL cho từng mục |
| **Kết quả thực tế** | ✅ PASS |

---

### TC-UI-07: Tab Health Monitor — Live Metrics

| Trường | Nội dung |
|--------|----------|
| **Test Case ID** | TC-UI-07 |
| **Mô tả** | Kiểm tra health metrics từ `/health` endpoint |
| **Bước thực hiện** | Vào tab "Kiểm Thử & Bảo Mật", xem Health Monitor |
| **Kết quả mong đợi** | Hiển thị uptime, ping, database type, environment |
| **Kết quả thực tế** | ✅ PASS |

---

## IV. Security Checklist

| # | Hạng mục | Trạng thái | Ghi chú |
|---|----------|------------|---------|
| 1 | Discord Token không hardcode trong code | ✅ | Load từ `.env` / biến môi trường |
| 2 | Gemini API Key không hardcode | ✅ | Load từ `GEMINI_API_KEY` env var |
| 3 | API Secret không hardcode (có default warning) | ✅ | Có default "changeme123" — cần đổi! |
| 4 | `.env` trong `.gitignore` | ✅ | Đã kiểm tra |
| 5 | `config.json` chứa token không commit | ⚠️ | Phải dùng `.env` thay thế |
| 6 | CORS header có trong API response | ✅ | Sau fix #34 |
| 7 | Rate Limiting API endpoint | ✅ | 30 req/phút/IP — sau fix #34 |
| 8 | Payload size validation | ✅ | Giới hạn 64KB — sau fix #34 |
| 9 | SQL Injection protection | ✅ | Dùng parameterized queries |
| 10 | Không log token/secret ra console | ✅ | Đã kiểm tra code |
| 11 | Health check endpoint public (không cần auth) | ✅ | `/health` không yêu cầu API key |
| 12 | Privilege Escalation: key phụ không thể UPDATE_CONFIG | ✅ | Chỉ `API_SECRET` (owner key) |
| 13 | DB_QUERY endpoint có thể bị lạm dụng | ⚠️ | Cần thêm whitelist query trong tương lai |

---

## V. Deployment Verification (Fix #33 — Long DevOps)

| Bước | Lệnh / Action | Kết quả mong đợi |
|------|---------------|------------------|
| 1 | Push code lên GitHub `main` | Render auto-deploy trigger |
| 2 | Render → Environment → Thêm `DATABASE_URL` (Neon) | Bot dùng PostgreSQL |
| 3 | Render → Environment → Thêm `DISCORD_TOKEN` | Bot kết nối Discord |
| 4 | Render → Environment → Thêm `API_SECRET` | Dashboard xác thực được |
| 5 | Mở `https://<render-url>/health` | JSON `"status": "ok"` |
| 6 | Render health check tự động ping `/health` mỗi 30 giây | Service stays "Live" |

---

*Tài liệu này được tạo bởi Viet (QA/QC) — Issue #34*  
*Cập nhật sau fix từ Long (DevOps — Issue #33)*
