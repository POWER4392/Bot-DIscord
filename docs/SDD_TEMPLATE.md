# TÀI LIỆU THIẾT KẾ CHI TIẾT HỆ THỐNG
(Software Design Document – SDD)

**Tên đề tài:** Xây dựng Discord Bot Quản Lý Server Tích Hợp AI
**Nhóm/Sinh viên thực hiện:** [Điền tên sinh viên/nhóm]
**Mã sinh viên:** [Điền mã sinh viên]
**Giảng viên hướng dẫn:** [Điền tên giảng viên]
**Lớp / Học kỳ:** [Điền Lớp/Học kỳ]
**Ngày hoàn thành:** [Điền ngày]

---

## Mục Lục
► Sinh viên sử dụng tính năng References → Table of Contents trong Word để tạo mục lục tự động khi nộp báo cáo.

## Danh sách Hình vẽ, Sơ đồ, Bảng, Biểu đồ
► Sinh viên sử dụng tính năng Insert Caption trong Word để tạo danh mục tự động.

## Các Task đã thực hiện
| Họ và tên | Nhiệm vụ | % Đóng góp | Ghi chú |
|---|---|---|---|
| [Điền Tên] | [Mô tả nhiệm vụ 1] | [...]% | [Ghi chú] |
| [Điền Tên] | [Mô tả nhiệm vụ 2] | [...]% | [Ghi chú] |
| [Điền Tên] | [Mô tả nhiệm vụ 3] | [...]% | [Ghi chú] |

---

## 1. Đặt vấn đề

### 1.1. Mô tả bài toán
Discord là nền tảng giao tiếp trực tuyến với hàng triệu máy chủ cộng đồng (servers). Tuy nhiên, việc quản lý một server quy mô lớn bằng phương pháp thủ công đòi hỏi rất nhiều thời gian và nhân lực. Quản trị viên (Admin/Moderator) thường xuyên phải đối mặt với các vấn đề như: tin nhắn rác (spam), lừa đảo (phishing), phá hoại máy chủ (nuking), cũng như nhu cầu cung cấp các tiện ích giải trí (âm nhạc, cấp độ) và hỗ trợ thành viên (ticket).
Bài toán đặt ra là xây dựng một hệ thống phần mềm (Discord Bot) có khả năng tự động hóa các tác vụ quản trị, kiểm duyệt nội dung theo thời gian thực và cung cấp các tính năng giải trí tích hợp trí tuệ nhân tạo (AI), giúp tối ưu hóa việc quản lý và phát triển cộng đồng trên Discord.

### 1.2. Mục đích
Tài liệu này (SDD) nhằm mục đích đặc tả chi tiết kiến trúc phần mềm, luồng dữ liệu, và thiết kế cơ sở dữ liệu của hệ thống Discord Bot. Tài liệu này cung cấp:
- Kiến trúc tổng quan và kiến trúc logic (Cog-based pattern) của Bot.
- Phương án triển khai trên nền tảng đám mây (Render, Neon PostgreSQL).
- Các kỹ thuật tích hợp API (Discord API, Google Gemini, YouTube API).
- Tạo cơ sở vững chắc cho các lập trình viên khác có thể bảo trì và mở rộng hệ thống trong tương lai.

### 1.3. Quy ước tài liệu
- **Bot/System:** Ứng dụng tự động do nhóm phát triển.
- **Server/Guild:** Máy chủ cộng đồng trên Discord.
- **Cog/Module:** Một thành phần mã nguồn độc lập chứa một nhóm chức năng (ví dụ: Music Cog, Moderation Cog).
- **AutoMod:** Hệ thống kiểm duyệt tự động.
- **GUI:** Giao diện người dùng đồ họa.

### 1.4. Các yêu cầu nghiệp vụ

#### 1.4.1. Nhóm chức năng Kiểm duyệt và Quản trị (Moderation)
- **Tự động kiểm duyệt (AutoMod):** Quét mọi tin nhắn để phát hiện và xóa các liên kết lừa đảo (Phishing), từ ngữ vi phạm (Blacklist) và hành vi gửi tin nhắn liên tục (Spam). Tự động cấm ngôn (Timeout) người vi phạm.
- **Bảo vệ chống phá hoại (Anti-Nuke):** Theo dõi tần suất xóa kênh, xóa vai trò. Nếu vượt ngưỡng (ví dụ: 3 lần/30 giây), lập tức tước toàn bộ quyền của thủ phạm.
- **Lệnh quản trị thủ công:** Cung cấp các lệnh cho Admin để Ban, Kick, Mute, Warn, Unban thành viên vi phạm.

#### 1.4.2. Nhóm chức năng Tiện ích cộng đồng (Utilities)
- **Hệ thống hỗ trợ (Ticket System):** Cho phép thành viên tạo kênh chat riêng tư với Ban quản trị để yêu cầu hỗ trợ.
- **Tạo kênh thoại tạm thời (Voice Generator):** Tự động tạo kênh thoại riêng khi thành viên tham gia sảnh chờ và xóa kênh đó khi không còn ai.
- **Nhận vai trò tự động (Reaction Roles):** Cung cấp giao diện nút bấm để thành viên tự gán hoặc gỡ bỏ vai trò (Role).

#### 1.4.3. Nhóm chức năng Giải trí và Tương tác (Entertainment & AI)
- **Phát nhạc (Music Player):** Phát âm thanh từ YouTube vào kênh thoại, hỗ trợ hàng đợi, bỏ qua bài hát và bảng điều khiển trực quan.
- **Hệ thống cấp độ (Leveling & Economy):** Tích lũy kinh nghiệm (XP) cho thành viên khi hoạt động, thăng cấp và nhận thưởng hằng ngày.
- **Chatbot AI (Gemini):** Tích hợp Google Gemini cho phép thành viên trò chuyện, hỏi đáp kiến thức bằng ngôn ngữ tự nhiên với Bot.

#### 1.4.4. Nhóm chức năng Theo dõi và Cấu hình (System)
- **Theo dõi mạng xã hội (Social Tracker):** Lấy dữ liệu tự động (Crawl) từ YouTube, TikTok, Reddit và thông báo lên Discord khi có bài đăng mới.
- **Cấu hình trực quan (Dashboard):** Giao diện Web/Desktop cho phép Admin tùy chỉnh Prefix, Token, bật/tắt module mà không cần can thiệp mã nguồn.

### 1.5. Yêu cầu phi nghiệp vụ

- **1.5.1. Hiệu năng:** Thời gian phản hồi lệnh của người dùng phải dưới 500ms (ngoại trừ các lệnh gọi API bên ngoài như tải nhạc hoặc hỏi AI).
- **1.5.2. Tính sẵn sàng:** Hệ thống Bot phải đạt thời gian hoạt động (Uptime) 99%, có cơ chế tự động khởi động lại khi gặp lỗi (thông qua Docker/Render).
- **1.5.3. Bảo mật:** Không lưu trữ trực tiếp mã thông báo (Token) hay API Keys trong mã nguồn. Phải sử dụng biến môi trường (`.env`). Các endpoint API của Dashboard phải có cơ chế xác thực.
- **1.5.4. Khả năng mở rộng:** Kiến trúc theo mẫu Plugin (Cogs) cho phép thêm tính năng mới bằng cách thả file Python vào thư mục mà không cần sửa đổi Core.
- **1.5.5. Tính tương thích đa nền tảng:** Hệ thống cơ sở dữ liệu hỗ trợ cả SQLite (phát triển cục bộ) và PostgreSQL (triển khai đám mây).
- **1.5.6. Ghi log:** Hệ thống phải ghi nhận chi tiết lỗi vào console và lưu vết (Audit Log) các thao tác kiểm duyệt trên Discord.

### 1.6. Các kỹ thuật áp dụng để giải quyết bài toán
- **Kiến trúc tổng thể:** Mô hình Hướng sự kiện (Event-Driven Architecture) kết hợp với kiến trúc Plugin (Cog Pattern) để xử lý bất đồng bộ. Giao tiếp giữa Dashboard và Bot thông qua IPC (Inter-Process Communication) bằng HTTP REST API.
- **Cơ sở dữ liệu:** Sử dụng `sqlite3` cho môi trường Local và dịch vụ Serverless PostgreSQL (`Neon.tech`) cho môi trường Production.
- **Phương án triển khai:** Triển khai Bot dưới dạng dịch vụ nền (Background Worker) trên nền tảng đám mây Render.com, sử dụng Nixpacks để đóng gói môi trường.
- **Bảo mật & AI:** Sử dụng Biểu thức chính quy (Regex) và thuật toán Sliding Window cho hệ thống AutoMod. Sử dụng API Google Gemini (`google-generativeai`) cho tính năng Chatbot.
- **Công cụ Frontend:** Giao diện Desktop sử dụng `customtkinter`, Web Dashboard sử dụng HTML/CSS/JS thuần kết hợp Fetch API.

---

## 2. Phân tích nghiệp vụ

### 2.1. Các lớp người dùng hệ thống
1. **Member (Thành viên phổ thông):** Có quyền gửi tin nhắn, tham gia kênh thoại, sử dụng các lệnh giải trí (phát nhạc, xem cấp độ, chat AI) và sử dụng tiện ích (tạo ticket, nhận vai trò).
2. **Moderator / Admin (Quản trị viên):** Có đặc quyền sử dụng các lệnh kiểm duyệt (Ban/Kick/Mute), can thiệp vào cài đặt của Bot, truy cập Web Dashboard.
3. **System (Tiến trình tự động):** Bản thân hệ thống Bot thực thi các tác vụ chạy ngầm như lọc từ ngữ, giám sát mạng xã hội.

### 2.2. Các đối tác nghiệp vụ và thừa tác viên
- **Discord API:** Đối tác cung cấp nền tảng giao tiếp, gửi/nhận sự kiện WebSocket và REST HTTP.
- **YouTube / Reddit / TikTok:** Nguồn cung cấp dữ liệu cho module Âm nhạc và Social Tracker.
- **Google AI:** Đối tác xử lý ngôn ngữ tự nhiên (NLP) cho chức năng Chatbot.

### 2.3. Các quy trình nghiệp vụ

#### 2.3.1. Quy trình dành cho Member
**2.3.1.1. Quy trình Yêu cầu Hỗ trợ (Tạo Ticket)**
- Mục tiêu: Liên hệ riêng tư với Ban quản trị.
- Các bước: Người dùng ấn nút "Tạo Ticket" -> Bot kiểm tra giới hạn -> Bot tạo kênh Private -> Tag Admin và người dùng vào kênh -> Trao đổi -> Admin ấn "Đóng" -> Bot xóa kênh.

**2.3.1.2. Quy trình Trò chuyện cùng AI**
- Mục tiêu: Hỏi đáp kiến thức.
- Các bước: Người dùng gõ `/chat <câu hỏi>` -> Bot gửi tín hiệu "Typing..." -> Hệ thống đẩy câu hỏi sang Google Gemini -> Nhận kết quả văn bản -> Bot phân mảnh văn bản (nếu > 2000 ký tự) -> Trả lời người dùng.

#### 2.3.2. Quy trình dành cho System (Hệ thống ngầm)
**2.3.2.1. Quy trình Kiểm duyệt Nội dung (AutoMod)**
- Mục tiêu: Giữ môi trường sạch.
- Các bước: Lắng nghe sự kiện `on_message` -> Bỏ qua tin của Admin/Bot -> Đối chiếu văn bản với chuỗi Regex Phishing -> Đối chiếu với Blacklist trong Database -> Tính toán tần suất tin nhắn (Spam) -> Nếu vi phạm: Xóa tin + Ban/Timeout + Gửi thông báo.

---

## 3. Phân tích yêu cầu

*(Sinh viên có thể chèn trực tiếp Bảng Use Case, Danh sách tác nhân từ file USE_CASES.md vào mục này).*

### 3.1. Xác định yêu cầu các bên liên quan
- **Admin:** Cần một công cụ thiết lập nhanh chóng, giao diện Dashboard thân thiện, chống lại các đợt tấn công phá hoại tự động.
- **Member:** Cần Bot phản hồi nhanh chóng khi phát nhạc, chất lượng âm thanh tốt, AI trả lời chính xác và thông minh.

### 3.2. Xác định actor
*(Tham khảo phần 2.1)*

### 3.3. Use Case Diagram
#### 3.3.1. Tổng quan hệ thống
► Hình 3.3.1: Use Case Diagram tổng quan (Sinh viên chèn ảnh chụp sơ đồ từ file USE_CASES.md vào đây).

#### 3.3.5. Đặc tả các ca sử dụng
► Sinh viên copy toàn bộ mục "4. Đặc tả Use Case Chi Tiết" từ file `USE_CASES.md` vào phần này. (Bao gồm đặc tả UC01, UC04, UC07, UC10, UC11).

#### 3.3.6. Biểu đồ hoạt động (Activity Diagram)
► Sinh viên sử dụng draw.io hoặc các công cụ UML để vẽ sơ đồ khối (Flowchart) cho: Luồng AutoMod, Luồng Phát nhạc và Luồng Xử lý AI, sau đó chèn hình ảnh vào đây.

---

## 4. Thiết kế hệ thống

### 4.1. Kiến trúc
Hệ thống sử dụng kiến trúc **Event-Driven Component-based**.
- **Tầng Giao tiếp (Gateway Layer):** Kết nối WebSocket với Discord để nhận sự kiện theo thời gian thực (tin nhắn, vào/ra kênh thoại).
- **Tầng Xử lý Lõi (Core Layer - `main.py`):** Điều phối các sự kiện, khởi tạo Database, duy trì HTTP API nội bộ.
- **Tầng Nghiệp vụ (Cogs Layer):** Chứa các module độc lập như Music, Moderation, Economy, Utilities. Mỗi Cog hoạt động độc lập và có thể nạp/gỡ (load/unload) linh hoạt.
- **Tầng Lưu trữ (Data Layer):** Lớp trừu tượng `core/database.py` kết nối xuống CSDL SQLite hoặc PostgreSQL.

### 4.2. Class và Sequence Diagram
► Sinh viên dùng phần mềm UML vẽ biểu đồ lớp (Class Diagram) đại diện cho Cấu trúc Cog của thư viện discord.py, và Biểu đồ tuần tự (Sequence Diagram) minh họa quá trình gửi lệnh`/play` phát nhạc.

### 4.3. Thiết kế giao diện
- **Giao diện người dùng trên Discord:** Sử dụng các thành phần Message Embed, Buttons, Select Menus do Discord hỗ trợ. (Ví dụ: Bảng điều khiển bài nhạc, Bảng Reaction Roles).
- **Giao diện Quản trị (Web Dashboard):** Trang SPA (Single Page Application) sử dụng HTML/CSS/JS. Giao diện tối màu (Dark mode) hiện đại.
► (Chèn hình ảnh chụp màn hình Web Dashboard và Panel Phát nhạc trên Discord vào đây).

### 4.4. Thiết kế cơ sở dữ liệu
Hệ thống sử dụng cơ sở dữ liệu quan hệ (RDBMS). Sơ đồ các bảng chính:
- **users (guild_id, user_id, xp, level):** Quản lý điểm kinh nghiệm, cấp độ của từng thành viên trong từng máy chủ. Khóa chính hợp nhất `(guild_id, user_id)`.
- **warnings (guild_id, user_id, warn_count):** Lưu trữ số lần cảnh cáo.
- **timed_roles (guild_id, user_id, role_id, expires_at):** Quản lý các vai trò có thời hạn (ví dụ: bị Mute trong 2 giờ).
- **reaction_panels (message_id, guild_id, roles_json):** Lưu cấu hình các bảng chọn vai trò tự động để khôi phục trạng thái (Persistent View) khi Bot khởi động lại.
- **gui_tasks (id, action, payload):** Hàng đợi công việc (Task Queue) dùng để trao đổi dữ liệu giữa Web Dashboard và Core Bot.
