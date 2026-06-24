# BÁO CÁO MÔN HỌC: CÔNG NGHỆ PHẦN MỀM
## Đề tài: Xây dựng Discord Bot Quản Lý Server Tích Hợp AI

---

| Thông tin | Chi tiết |
|-----------|----------|
| **Môn học** | Công Nghệ Phần Mềm |
| **Đề tài** | Discord Bot Quản Lý Server Tích Hợp AI |
| **Ngôn ngữ** | Python 3.x |
| **Thư viện chính** | discord.py, aiohttp, yt-dlp, Pillow, SQLite/PostgreSQL |
| **Nền tảng** | Discord API |
| **Thành viên nhóm** | - **Trần Đức Mạnh** (`POWER4392`) - Backend Developer<br>- **Đỗ Hoàng Long** (`Long432`) - DevOps & PM<br>- **Mai Văn Việt** (`vanviet2k6-creator`) - QA & Security<br>- **Tống Xuân Nghĩa** (`hendrix810`) - UI/UX & Content<br>- **Nguyễn Đức Duy** (`duynguyen1012`) - AI/ML & Features |

---

## 1. GIỚI THIỆU DỰ ÁN

### 1.1 Bối cảnh

Discord là nền tảng giao tiếp trực tuyến phổ biến với hàng triệu server cộng đồng. Việc quản lý server thủ công tốn nhiều công sức của các quản trị viên. Dự án này nhằm xây dựng một **Discord Bot thông minh (All-In-One)** có khả năng tự động hóa việc quản lý server, tích hợp các tính năng AI và automation để hỗ trợ cộng đồng hiệu quả hơn.

### 1.2 Mục tiêu

- Tự động hóa công tác kiểm duyệt nội dung (AutoMod)
- Phát hiện và ngăn chặn spam, phishing bằng AI pattern matching
- Hệ thống theo dõi mạng xã hội tự động
- Cung cấp tiện ích giải trí (âm nhạc, kinh tế, cấp độ)
- Giao diện cấu hình trực quan (GUI)

### 1.3 Đội ngũ phát triển & Phân chia nhiệm vụ

Dự án được thực hiện bởi nhóm gồm 5 thành viên với vai trò và nhiệm vụ cụ thể như sau:

1. **Trần Đức Mạnh** (`POWER4392`) **– Backend Developer (Lập trình cốt lõi Backend):**
   - Thiết kế kiến trúc Bot (Main Core, Command & Event Handler).
   - Lập trình các tính năng/Cogs cốt lõi (như Moderation, Utilities, Music Player).
   - Xây dựng lớp trừu tượng cơ sở dữ liệu (`core/database.py` hỗ trợ SQLite & PostgreSQL).
   - Thiết lập API HTTP nội bộ (IPC server) để kết nối giữa GUI và Bot.
   - Bàn giao mã nguồn hoàn chỉnh cho thành viên kiểm thử và triển khai.

2. **Đỗ Hoàng Long** (`Long432`) **– DevOps & Cloud Deployment (Triển khai & Quản trị dự án):**
   - Trưởng nhóm, quản trị tiến độ dự án và điều phối công việc giữa các thành viên.
   - Nghiên cứu giải pháp, cấu hình môi trường và triển khai bot lên Render Cloud Hosting.
   - Quản trị cơ sở dữ liệu đám mây Neon Serverless PostgreSQL.
   - Thiết lập UptimeRobot để giám sát Uptime 24/7 và viết tài liệu báo cáo dự án (`BAO_CAO_CNPM.md`).

3. **Mai Văn Việt** (`vanviet2k6-creator`) **– QA & Security Engineer (Kiểm thử & Bảo mật):**
   - Lập kịch bản kiểm thử (Test Cases) chi tiết cho từng tính năng của bot.
   - Chạy thử nghiệm local và cloud (Black-box & White-box testing) để tìm và ghi nhận log lỗi.
   - Đảm bảo an toàn bảo mật thông tin, quản lý file cấu hình `.env`, `config.json` và `config.example.json`.
   - Kiểm thử chịu tải hệ thống (anti-spam, anti-nuke).

4. **Tống Xuân Nghĩa** (`hendrix810`) **– UI/UX & Content Designer (Thiết kế Giao diện & Nội dung):**
   - Thiết kế giao diện GUI điều khiển Desktop (`setting_gui.py`) bằng `customtkinter`.
   - Phác thảo giao diện Web Dashboard quản lý bot (định hướng tuần kế tiếp).
   - Thiết kế trải nghiệm hiển thị trên Discord: định dạng các tin nhắn nhúng (Embeds), nút bấm (Buttons), thanh chọn (Select Menus) của bot để tăng tính thẩm mỹ và thân thiện với người dùng.
   - Hỗ trợ biên soạn bộ câu lệnh mẫu và tài liệu phản hồi của Bot.

5. **Nguyễn Đức Duy** (`duynguyen1012`) **– AI/ML & Feature Integration Engineer (Tích hợp AI & Tính năng mở rộng):**
   - Xây dựng thuật toán kiểm duyệt nội dung tự động nâng cao (Regex scam detection, Sliding Window anti-spam).
   - Thiết lập hệ thống Crawl tin tức tự động (`cogs/social.py`) từ YouTube, TikTok, Reddit.
   - Lập trình hệ thống tích hợp XP & Cấp độ và thuật toán Gamification (`cogs/economy.py`).
   - Nghiên cứu tích hợp API Gemini/GPT để phát triển Chatbot AI phản hồi thông minh trong tuần tới.

---

## 2. PHÂN TÍCH YÊU CẦU

### 2.1 Yêu cầu chức năng

#### Nhóm Quản Lý & Kiểm Duyệt
| ID | Yêu cầu | Mức độ ưu tiên |
|----|---------|---------------|
| F01 | Phát hiện và xóa link Phishing/Scam tự động | Cao |
| F02 | Chống spam (>5 tin/3.5 giây → Timeout 5 phút) | Cao |
| F03 | Bộ lọc từ ngữ theo Blacklist | Cao |
| F04 | Anti-Nuke: phát hiện xóa kênh/role hàng loạt | Cao |
| F05 | Lệnh Kick, Ban, Mute, Unban, Warn | Cao |
| F06 | Hệ thống Cảnh cáo (3 warn = Timeout, 5 warn = Kick) | Trung bình |
| F07 | Log tin nhắn bị xóa/sửa | Trung bình |

#### Nhóm Tiện Ích
| ID | Yêu cầu | Mức độ ưu tiên |
|----|---------|---------------|
| F08 | Hệ thống Ticket hỗ trợ | Cao |
| F09 | Kênh thoại tạm thời (Voice Generator) | Trung bình |
| F10 | Panel chọn Role tự động (Reaction Roles) | Trung bình |
| F11 | Phát nhạc YouTube | Trung bình |
| F12 | Hệ thống XP & Cấp độ | Thấp |
| F13 | Theo dõi mạng xã hội (YouTube, TikTok, Reddit, Facebook) | Trung bình |

#### Nhóm Cấu Hình
| ID | Yêu cầu | Mức độ ưu tiên |
|----|---------|---------------|
| F14 | GUI cấu hình (customtkinter) | Cao |
| F15 | Hỗ trợ nhiều server cùng lúc | Cao |
| F16 | API HTTP nội bộ (IPC giữa GUI và Bot) | Trung bình |

### 2.2 Yêu cầu phi chức năng

- **Hiệu năng:** Bot phản hồi lệnh < 500ms
- **Độ tin cậy:** Uptime 24/7, auto-restart khi lỗi
- **Bảo mật:** Token không được lộ, config lưu local
- **Khả năng mở rộng:** Kiến trúc Cog-based, dễ thêm tính năng
- **Tương thích:** SQLite (local dev) và PostgreSQL (Neon Serverless PostgreSQL trên cloud, được host trên Render và giám sát qua UptimeRobot)

---

## 3. THIẾT KẾ HỆ THỐNG

### 3.1 Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────┐
│                    DISCORD API                          │
└──────────────────────┬──────────────────────────────────┘
                       │ discord.py (WebSocket + REST)
┌──────────────────────▼──────────────────────────────────┐
│                    main.py (Bot Core)                   │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Task Loop  │  │ Event Handler│  │  setup_hook()   │  │
│  │ (1 min)    │  │ on_ready()   │  │  Load Cogs      │  │
│  └────────────┘  └──────────────┘  └─────────────────┘  │
└──────────┬──────────────────────────────────────────────┘
           │ Cog Extensions
  ┌────────┴──────────────────────────────────────────┐
  │  cogs/moderation.py  │  cogs/utilities.py         │
  │  cogs/music.py       │  cogs/economy.py           │
  │  cogs/social.py      │                            │
  └────────┬──────────────────────────────────────────┘
           │ Core Services
  ┌────────┴──────────────────────────────────────────┐
  │  core/database.py    │  core/api_server.py        │
  │  core/shared.py      │                            │
  └────────┬──────────────────────────────────────────┘
           │
  ┌────────┴──────────────────────────────────────────┐
  │        SQLite (local)  /  PostgreSQL (cloud)       │
  └───────────────────────────────────────────────────┘
           ▲
           │ HTTP API (localhost)
  ┌────────┴──────────────────────────────────────────┐
  │         setting_gui.py (GUI Desktop App)           │
  └───────────────────────────────────────────────────┘
```

### 3.2 Mô hình dữ liệu (Database Schema)

```sql
-- Người dùng: XP và cấp độ
users (guild_id, user_id, xp, level)

-- Cảnh cáo thành viên
warnings (guild_id, user_id, warn_count)

-- Role tạm thời có hạn
timed_roles (guild_id, user_id, role_id, expires_at)

-- Blacklist từ ngữ
blacklists (guild_id, word)

-- Panel chọn role
reaction_panels (message_id, guild_id, roles_json)

-- Theo dõi mạng xã hội
social_tracker (guild_id, platform, target_id, channel_id, ping_role, last_post_id)

-- Hàng đợi lệnh từ GUI
gui_tasks (id, action, payload)
```

### 3.3 Luồng xử lý AutoMod (AI Pattern Matching)

```
Tin nhắn đến
     │
     ▼
Có phải Bot? ──(Có)──► Bỏ qua
     │ (Không)
     ▼
Có quyền Mod/Admin? ──(Có)──► Bỏ qua AutoMod
     │ (Không)
     ▼
Khớp SCAM_REGEX? ──(Có)──► Xóa + Timeout 1h + Log
     │ (Không)
     ▼
Spam > 5 tin/3.5s? ──(Có)──► Xóa + Timeout 5p + Log
     │ (Không)
     ▼
Có từ trong Blacklist? ──(Có)──► Xóa + Timeout + Log
     │ (Không)
     ▼
Xử lý bình thường
```

### 3.4 Luồng Anti-Nuke

```
Sự kiện: Xóa kênh/role
     │
     ▼
Đọc Audit Log → Lấy thủ phạm
     │
     ▼
Lưu timestamp vào tracker[guild][user]
     │
     ▼
Đếm hành động trong 30 giây
     │
     ├── < 3 lần ──► Bỏ qua
     │
     └── ≥ 3 lần ──► Xóa toàn bộ Role của thủ phạm + Gửi cảnh báo
```

---

## 4. CÔNG NGHỆ SỬ DỤNG

### 4.1 Ngôn ngữ & Framework

| Công nghệ | Phiên bản | Mục đích |
|-----------|-----------|---------|
| Python | 3.10+ | Ngôn ngữ lập trình chính |
| discord.py | 2.x | Discord API wrapper |
| aiohttp | Latest | Async HTTP server (API nội bộ) |
| yt-dlp | 2025+ | Tải nhạc YouTube |
| Pillow | Latest | Tạo ảnh Rank Card |
| customtkinter | Latest | GUI cấu hình |
| SQLite3 | Built-in | Lưu trữ local |
| PostgreSQL (Neon) | 14+ | Lưu trữ cloud (Serverless PostgreSQL trên Neon.tech) |

### 4.2 Ứng dụng AI trong Bot

Bot sử dụng các kỹ thuật AI/ML sau:

#### a) Phát hiện Phishing bằng Regex Pattern Matching
```python
SCAM_REGEX_GLOBAL = re.compile(
    r'(free\s*nitro|discord\.gift|steamcommunity\.(?!com)|'
    r'bit\.ly|tinyurl\.com|steam.*free|gift.*steam|'
    r'click.*here.*free|win.*prize)', 
    re.IGNORECASE
)
```
Hệ thống sử dụng **Regular Expression nâng cao** để phát hiện các mẫu URL và văn bản phishing phổ biến. Đây là dạng **Rule-Based AI** – hệ thống chuyên gia dựa trên tri thức về các mẫu tấn công đã biết.

#### b) Phát hiện Spam bằng Sliding Window Algorithm
```
Thuật toán:
- Mỗi tin nhắn được đánh dấu timestamp
- Cửa sổ trượt 3.5 giây: lọc các tin nhắn cũ hơn 3.5s
- Nếu > 5 tin trong cửa sổ → phát hiện spam
```
Đây là **Anomaly Detection** đơn giản nhưng hiệu quả, không cần training data.

#### c) Anti-Nuke Detection
```
Thuật toán:
- Theo dõi tần suất hành động xóa kênh/role
- Cửa sổ thời gian: 30 giây
- Ngưỡng phát hiện: ≥ 3 hành động
- Phản ứng: Thu hồi toàn bộ quyền hạn
```

#### d) Hệ thống XP & Level-Up (Gamification AI)
```python
# Công thức tính level
level = max(1, int((xp / 100) ** (1/1.5)))
```
Sử dụng hàm mũ để tạo đường cong tăng trưởng phi tuyến – người chơi cần ngày càng nhiều XP hơn để lên cấp cao hơn.

#### e) Social Media Monitoring (Crawler tự động)
Bot tự động crawler dữ liệu từ:
- **YouTube**: RSS Feed XML (`feeds/videos.xml`)
- **Reddit**: JSON API (`/r/{sub}/new.json`)
- **TikTok**: RSSHub RSS feed
- **Facebook**: RSS/Atom Feed

Cơ chế polling 5 phút/lần, so sánh `last_post_id` để phát hiện nội dung mới.

---

## 5. CẤU TRÚC DỰ ÁN

```
Bot/
├── main.py                  # Entry point, khởi động bot
├── setting_gui.py           # GUI cấu hình (customtkinter)
├── requirements.txt         # Dependencies
├── config.json              # Cấu hình bot (token, prefix...)
│
├── cogs/                    # Các module tính năng (Cog Pattern)
│   ├── moderation.py        # AutoMod, Kick/Ban/Mute, Anti-Nuke
│   ├── utilities.py         # Ticket, Voice, Role Panel
│   ├── music.py             # Phát nhạc YouTube
│   ├── economy.py           # XP, Level, Daily reward
│   └── social.py            # Theo dõi MXH tự động
│
├── core/                    # Dịch vụ nền tảng
│   ├── database.py          # SQLite/PostgreSQL abstraction layer
│   ├── api_server.py        # HTTP API server (IPC)
│   └── shared.py            # Biến toàn cục, config loader
│
└── databases/               # File database SQLite
    └── bot_core.db
```

---

## 6. CÁC PATTERN THIẾT KẾ ĐÃ ÁP DỤNG

### 6.1 Cog Pattern (Plugin Architecture)
Mỗi nhóm tính năng được đóng gói thành một **Cog** (plugin) riêng biệt. Bot có thể load/unload từng Cog độc lập mà không ảnh hưởng đến các phần khác.

```python
# Đăng ký Cog
await bot.load_extension("cogs.moderation")
await bot.load_extension("cogs.utilities")
```

**Lợi ích:** Dễ bảo trì, dễ mở rộng, tách biệt mối quan tâm (Separation of Concerns).

### 6.2 Observer Pattern (Event-Driven)
Bot lắng nghe các sự kiện Discord và phản ứng tương ứng:

```python
@commands.Cog.listener()
async def on_message(self, message): ...

@commands.Cog.listener()
async def on_guild_channel_delete(self, channel): ...
```

### 6.3 Database Abstraction Layer
`core/database.py` cung cấp interface thống nhất cho cả SQLite và PostgreSQL. Code ở tầng trên không cần biết đang dùng DB nào.

```python
# SQLite query: dùng ?
cursor.execute("SELECT * FROM users WHERE guild_id=?", (guild_id,))

# PostgreSQL: tự động chuyển sang %s
query = query.replace("?", "%s")
```

### 6.4 IPC Pattern (Inter-Process Communication)
GUI và Bot giao tiếp qua:
- **HTTP API** (aiohttp server chạy trong asyncio loop)
- **Database Queue** (`gui_tasks` table): GUI ghi task → Bot đọc và thực thi mỗi 3 giây

### 6.5 Persistent View Pattern
Discord.py Views có thể bị mất sau khi bot restart. Bot đăng ký lại tất cả Views khi khởi động:

```python
bot.add_view(TicketView())
bot.add_view(PersistentRoleView(roles_data, f"rr_panel_{msg_id}"))
```

---

## 7. PHÂN TÍCH RỦI RO

| Rủi ro | Xác suất | Mức độ ảnh hưởng | Giải pháp |
|--------|----------|-----------------|-----------|
| Token bị lộ | Thấp | Cao | Lưu trong `config.json`, thêm vào `.gitignore` |
| Bot bị rate-limit | Trung bình | Trung bình | Sử dụng `asyncio`, tránh gọi API đồng bộ |
| Database corruption | Thấp | Cao | Sử dụng `db_lock` (threading.Lock) |
| Discord API thay đổi | Thấp | Cao | Cập nhật discord.py thường xuyên |
| Crawler bị chặn | Trung bình | Thấp | Thêm User-Agent, retry logic |

---

## 8. KẾT QUẢ & ĐÁNH GIÁ

### 8.1 Tính năng đã hoàn thành

| # | Tính năng | Trạng thái |
|---|-----------|-----------|
| 1 | AutoMod (Phishing, Spam, Blacklist) | ✅ Hoàn thành |
| 2 | Anti-Nuke Protection | ✅ Hoàn thành |
| 3 | Kick / Ban / Mute / Warn | ✅ Hoàn thành |
| 4 | Hệ thống Ticket | ✅ Hoàn thành |
| 5 | Voice Generator (kênh thoại tạm) | ✅ Hoàn thành |
| 6 | Reaction Role Panel | ✅ Hoàn thành |
| 7 | Social Media Monitoring | ✅ Hoàn thành |
| 8 | Phát nhạc YouTube | ✅ Hoàn thành |
| 9 | Hệ thống XP & Cấp độ | ✅ Hoàn thành |
| 10 | GUI Cấu hình | ✅ Hoàn thành |
| 11 | Multi-server support | ✅ Hoàn thành |
| 12 | Cloud deployment (Render & Neon & UptimeRobot) | ✅ Hoàn thành (Uptime 24/7) |
| 13 | Chatbot AI tích hợp Gemini SDK (Flash 1.5, Vision, RAG) | ✅ Hoàn thành |
| 14 | Web Dashboard quản trị trực quan & vẽ biểu đồ (Chart.js) | ✅ Hoàn thành |
| 15 | Tự động hóa CI/CD Deploy & Bộ kịch bản Test Suite | ✅ Hoàn thành (Release 0.1.0) |

### 8.2 Điểm nổi bật kỹ thuật

1. **Dual Database Support**: Tự động chọn SQLite (local dev) hoặc PostgreSQL (cloud) dựa trên biến môi trường `DATABASE_URL`.

2. **Thread-Safe Database**: Sử dụng `threading.Lock` (`db_lock`) để tránh race condition khi nhiều async task truy cập database đồng thời.

3. **Async-First Architecture**: Toàn bộ I/O đều là async, tránh blocking event loop. Các tác vụ blocking (DB query) được chạy qua `run_in_executor`.

4. **Graceful Degradation**: Nếu một tính năng lỗi (vd: không lấy được audit log), bot vẫn tiếp tục hoạt động bình thường.

---

## 9. KẾT LUẬN

Dự án **Discord Bot All-In-One** đã thành công xây dựng một hệ thống phần mềm phức tạp, tích hợp nhiều công nghệ hiện đại:

- **AI/ML**: Pattern matching, anomaly detection, gamification algorithm, Gemini conversational AI & Vision.
- **Backend**: Async Python, dual database, REST API.
- **Frontend**: Desktop GUI (customtkinter) và Web Dashboard (HTML/CSS/JS/Chart.js).
- **DevOps**: Cloud deployment trên Render, CSDL Neon PostgreSQL, giám sát tự động 24/7 qua UptimeRobot, CI/CD tự động qua GitHub Actions.

Bot đang hoạt động ổn định trên môi trường production với khả năng phục vụ nhiều Discord server cùng lúc, tự động hóa 90% công tác quản lý server thông thường.

### 9.1 Kế hoạch bảo trì và phát triển tiếp theo

Sau khi phát hành phiên bản **Release 0.1.0**, định hướng phát triển tiếp theo của dự án bao gồm:

1. **Bảo mật**: Nâng cấp cơ chế xác thực cho Web Dashboard sử dụng OAuth2 trực tiếp qua tài khoản Discord.
2. **Hiệu năng & Chi phí**: Tối ưu hóa bộ nhớ đệm (Caching) cho dữ liệu chatbot AI nhằm giảm tần suất gọi API Gemini, tối thiểu hóa chi phí token.
3. **Mở rộng tính năng**: Phát triển thêm tính năng sao lưu (Backup) cấu hình server tự động lên đám mây.
4. **Vận hành**: Tiếp tục giám sát và xử lý lỗi phát sinh (nếu có) trên production qua log hệ thống.

---

## TÀI LIỆU THAM KHẢO

1. discord.py Documentation – https://discordpy.readthedocs.io/
2. Discord Developer Portal – https://discord.com/developers/docs/
3. Python asyncio Documentation – https://docs.python.org/3/library/asyncio.html
4. PostgreSQL Documentation – https://www.postgresql.org/docs/
5. YouTube Data API v3 – https://developers.google.com/youtube/v3
6. Design Patterns: Elements of Reusable Object-Oriented Software – GoF (1994)

---

*Báo cáo được tạo cho môn Công Nghệ Phần Mềm | Năm học 2025-2026*
