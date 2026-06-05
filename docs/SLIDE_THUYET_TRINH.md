# SLIDE THUYẾT TRÌNH DỰ ÁN DISCORD BOT QUẢN LÝ SERVER TÍCH HỢP AI
## Môn học: Công Nghệ Phần Mềm | Nhóm: 5 Thành Viên

---

### [SLIDE 1] TIÊU ĐỀ & GIỚI THIỆU NHÓM
* **Tiêu đề Slide:** Đề tài: Xây dựng Discord Bot Quản Lý Server Tích Hợp AI
* **Nội dung:**
  - **Môn học:** Công Nghệ Phần Mềm
  - **Thành viên Nhóm 5:**
    - **Trần Đức Mạnh** (Backend Developer) - Lập trình core bot, API server, DB abstraction layer.
    - **Đỗ Hoàng Long** (PM & DevOps) - Quản trị tiến độ, CI/CD, hosting Render, Neon PG.
    - **Mai Văn Việt** (QA & Security) - Lập kịch bản test case, security audit, stress test.
    - **Tống Xuân Nghĩa** (UI/UX & Content) - Thiết kế GUI Desktop & Web Dashboard, soạn kịch bản.
    - **Nguyễn Đức Duy** (AI/ML & Features) - Lập trình AI Chatbot, anti-spam sliding window.

---

### [SLIDE 2] BỐI CẢNH & ĐẶT VẤN ĐỀ
* **Tiêu đề Slide:** Bối cảnh và Thử thách thực tế
* **Nội dung:**
  - Sự bùng nổ của các cộng đồng Discord lớn đặt ra áp lực quản lý cực kỳ nặng nề cho các Quản trị viên (Moderators).
  - Các vụ lừa đảo (phishing link), spam tin nhắn, phá hoại server (nuke server) diễn ra với tốc độ cực nhanh, con người không thể xử lý thủ công kịp thời.
  - Các bot hiện tại thường rời rạc: chỉ có tính năng nhạc, chỉ có mod hoặc chỉ có chatbot riêng biệt.
  - Cần một giải pháp **All-In-One** tích hợp sâu AI để tự động hóa và tối ưu trải nghiệm người dùng.

---

### [SLIDE 3] MỤC TIÊU DỰ ÁN
* **Tiêu đề Slide:** Mục tiêu Hệ thống
* **Nội dung:**
  - **Tự động hóa hoàn toàn:** Phát hiện spam, link lừa đảo bằng thuật toán AI và regex nâng cao.
  - **Tối ưu trải nghiệm:** Độc lập quản lý vai trò tự chọn (Reaction Roles), kênh thoại tạm thời (Voice Generator), hệ thống ticket hỗ trợ trực quan.
  - **Trải nghiệm giải trí tốt:** Hệ thống phát nhạc chất lượng cao từ YouTube và cơ chế tính điểm hoạt động (Gamification XP/Level).
  - **Cấu hình đa dạng:** Quản lý tập trung qua GUI Desktop và Web Dashboard thông qua REST API kết nối thời gian thực.

---

### [SLIDE 4] KIẾN TRÚC TỔNG QUAN
* **Tiêu đề Slide:** Kiến trúc Hệ thống
* **Nội dung:**
  - **Mô hình kiến trúc:** Client - Server - Database & Gateway.
  - **Discord API (WebSocket/REST):** Giao diện tương tác chính của người dùng với Bot.
  - **Main Bot Core (Python):** Quản lý vòng lặp sự kiện (Event Loop), cơ chế nạp Cog dynamic (Plugin Pattern).
  - **IPC HTTP Server (aiohttp):** Lắng nghe yêu cầu thay đổi cấu hình hoặc gửi tin nhắn từ GUI và Web Dashboard.
  - **Dual Database Layer:** SQLite cho môi trường phát triển local, tự động chuyển đổi sang PostgreSQL khi triển khai cloud.

---

### [SLIDE 5] THIẾT KẾ CƠ SỞ DỮ LIỆU
* **Tiêu đề Slide:** Mô hình Cơ sở dữ liệu (Database Schema)
* **Nội dung:**
  - Thiết kế các bảng dữ liệu chuẩn hóa đảm bảo tính nhất quán (ACID):
    - `users`: Theo dõi XP, Cấp độ của người dùng.
    - `warnings`: Lưu trữ số lần cảnh cáo vi phạm của thành viên.
    - `timed_roles`: Quản lý vai trò có thời hạn (VIP, Mute, Timeout).
    - `blacklists`: Danh sách các từ ngữ bị cấm trên server.
    - `reaction_panels`: Lưu trữ cấu trúc nút bấm tự chọn vai trò.
    - `social_tracker`: Cấu hình crawling tự động từ các mạng xã hội.

---

### [SLIDE 6] TÍNH NĂNG KIỂM DUYỆT & AUTOMOD
* **Tiêu đề Slide:** Cơ chế bảo vệ Server tự động
* **Nội dung:**
  - **AutoMod:** Tích hợp bộ lọc Regex nâng cao phát hiện liên kết lừa đảo Nitro giả, giftcode giả mạo.
  - **Anti-Spam:** Sử dụng thuật toán cửa sổ trượt (Sliding Window Algorithm) phát hiện spam nhanh hơn 5 tin/3.5s.
  - **Blacklist:** Lọc nội dung thô tục, tự động xóa tin nhắn vi phạm và log lại hành vi.
  - **Anti-Nuke:** Theo dõi số lượng hành động xóa kênh/role của các quản trị viên trong 30s. Nếu phát hiện hành động bất thường, lập tức thu hồi toàn bộ quyền hạn.

---

### [SLIDE 7] THUẬT TOÁN AUTOMOD: CỬA SỔ TRƯỢT (SLIDING WINDOW)
* **Tiêu đề Slide:** Ứng dụng AI/ML: Phát hiện bất thường (Anomaly Detection)
* **Nội dung:**
  - Cách hoạt động của thuật toán cửa sổ trượt:
    1. Mỗi tin nhắn của người dùng được gán một dấu thời gian (timestamp).
    2. Một hàng đợi (queue) lưu trữ lịch sử tin nhắn của từng người dùng.
    3. Khi có tin nhắn mới, hệ thống dọn dẹp các tin nhắn cũ vượt quá cửa sổ 3.5 giây.
    4. Đo lường kích thước hàng đợi: nếu vượt quá 5 tin nhắn → Trạng thái bất thường (Spam).
    5. Bot thực hiện hành động trừng phạt: Xóa tin nhắn, timeout tài khoản 5 phút và ghi nhận log gửi về kênh Admin.

---

### [SLIDE 8] TÍCH HỢP CHATBOT AI GEMINI
* **Tiêu đề Slide:** Đàm thoại thông minh thông qua Gemini API
* **Nội dung:**
  - Tích hợp mô hình ngôn ngữ lớn **Gemini-1.5-Flash** mang lại câu trả lời tự nhiên, chính xác cho thành viên.
  - Hỗ trợ **System Prompt** động, cho phép Quản trị viên thay đổi tính cách, phong cách giao tiếp của Bot thông qua GUI/Web Dashboard.
  - **Cơ chế hoạt động:** Lắng nghe sự kiện trong kênh trò chuyện được chỉ định hoặc mention.
  - Tự động bỏ qua các bot khác và kiểm tra quyền hạn trước khi trả lời.
  - Xử lý lỗi mềm dẻo (Graceful Degradation) khi lỗi mạng hoặc thiếu API Key để tránh làm bot bị crash.

---

### [SLIDE 9] HỆ THỐNG TIỆN ÍCH & GIẢI TRÍ
* **Tiêu đề Slide:** Tiện ích và Giải trí
* **Nội dung:**
  - **Hệ thống Phát nhạc:** Tích hợp `yt-dlp` và `ffmpeg` cho phép phát nhạc chất lượng cao trực tiếp từ YouTube. Điều khiển trực quan bằng nút bấm (Pause, Resume, Skip, Queue).
  - **Hệ thống Ticket:** Cho phép người dùng click nút để tạo một kênh riêng hỗ trợ kỹ thuật, tự động lưu trữ log hỗ trợ.
  - **Kênh thoại tạm thời:** Khi người dùng tham gia kênh thoại chính, bot tự động tạo kênh riêng và xóa đi khi không có người sử dụng.
  - **Hệ thống Cấp độ:** Tự động cộng XP dựa trên hoạt động nhắn tin, tạo thẻ xếp hạng cá nhân bằng thư viện Pillow.

---

### [SLIDE 10] CƠ CHẾ ĐỒNG BỘ IPC (INTER-PROCESS COMMUNICATION)
* **Tiêu đề Slide:** Kết nối giữa GUI điều khiển và Bot Core
* **Nội dung:**
  - Bot Core chạy bất đồng bộ bằng `asyncio`, GUI Tkinter chạy trên luồng chính.
  - Giao tiếp hai chiều thông qua:
    1. **HTTP REST API (aiohttp):** GUI gọi API GET/POST để đồng bộ cấu hình, lấy danh sách Server/Kênh và trạng thái ping thời gian thực.
    2. **Hàng đợi Database (gui_tasks):** Các tác vụ phức tạp (như gửi tin nhắn) được GUI ghi vào DB. Bot Core quét bảng `gui_tasks` mỗi 3 giây để thực thi một cách an toàn tránh xung đột luồng (Race Condition).
  - Sử dụng khóa đồng bộ `db_lock` (`threading.Lock`) để đảm bảo an toàn truy cập DB đồng thời.

---

### [SLIDE 11] GIAO DIỆN WEB DASHBOARD PORTAL
* **Tiêu đề Slide:** Trải nghiệm Quản trị từ xa bằng Web Dashboard
* **Nội dung:**
  - Nâng cấp từ GUI Tkinter truyền thống lên giao diện web hiện đại.
  - **Ngôn ngữ phát triển:** HTML5, CSS3 và Vanilla JS cho hiệu suất tải trang cực nhanh (< 200ms).
  - **Thiết kế giao diện:** Phong cách **Dark Glassmorphism** cao cấp, các góc bo tròn mềm mại, chuyển động mượt mà (smooth micro-animations).
  - **Tính năng chính:**
    - Xem nhanh biểu đồ tài nguyên (Servers, Users, Voice, Ping).
    - Cấu hình Gemini AI trực tiếp từ trình duyệt.
    - Bộ tạo bảng chọn Role (Reaction Roles) kéo thả/nút bấm linh hoạt.
    - Soạn thảo và lưu trực tiếp tệp `config.json`.

---

### [SLIDE 12] KẾ HOẠCH KIỂM THỬ (QA)
* **Tiêu đề Slide:** Đảm bảo chất lượng hệ thống (Quality Assurance)
* **Nội dung:**
  - Chạy thử nghiệm song song trên cả môi trường local và cloud thông qua bộ kịch bản kiểm thử:
    - **TC-AI-01:** Kiểm tra hội thoại thông thường -> **ĐẠT**
    - **TC-AI-02:** Xử lý ngoại lệ khi thiếu API Key -> **ĐẠT**
    - **TC-API-01:** Lấy số liệu stats của Web Dashboard -> **ĐẠT**
    - **TC-API-02:** Xác thực API bằng token sai -> **ĐẠT** (Trả về lỗi 401)
  - Sử dụng Chrome DevTools mô phỏng responsive để đảm bảo giao diện web hiển thị tốt trên cả màn hình Desktop lớn và màn hình điện thoại di động.

---

### [SLIDE 13] QUY TRÌNH TRIỂN KHAI (DEVOPS)
* **Tiêu đề Slide:** Triển khai Hệ thống và Giám sát Uptime 24/7
* **Nội dung:**
  - **Môi trường Deploy:** Render Cloud Hosting (Web Service).
  - **Hệ cơ sở dữ liệu:** Neon Serverless PostgreSQL Cloud Database.
  - **CI/CD:** Thiết lập cấu hình tự động triển khai thông qua liên kết GitHub Repository.
  - **Giám sát hoạt động:** Cấu hình UptimeRobot tự động gửi gói tin ping đến server mỗi 5 phút một lần để giữ ứng dụng luôn thức (Uptime 24/7), khắc phục nhược điểm ngủ đông của Render Free Tier.

---

### [SLIDE 14] ĐÁNH GIÁ RỦI RO & BẢO MẬT
* **Tiêu đề Slide:** Quản trị rủi ro & Bảo mật hệ thống
* **Nội dung:**
  - **Rò rỉ thông tin nhạy cảm:** Token bot và mật khẩu DB được chuyển hoàn toàn vào biến môi trường (`.env`), cấu hình `.gitignore` loại bỏ tuyệt đối các tệp này khỏi git commit.
  - **Tấn công SQL Injection:** Đảm bảo 100% các câu lệnh SQL được tham số hóa (Parameterized Queries).
  - **Tấn công chiếm quyền API:** Triển khai header xác thực bắt buộc `X-API-Key`. Chỉ những API request có key chính xác mới được truy cập dữ liệu hệ thống.

---

### [SLIDE 15] KẾT LUẬN & ĐỊNH HƯỚNG TƯƠNG LAI
* **Tiêu đề Slide:** Kết luận & Lộ trình phát triển tuần tiếp theo (Sprint 3.2)
* **Nội dung:**
  - **Kết quả đạt được:** Dự án đã xây dựng thành công bộ công cụ Discord Bot toàn diện, vận hành ổn định trên đám mây đám ứng 12/12 tiêu chí chức năng đặt ra.
  - **Định hướng Sprint 3.2 (Tuần tiếp theo):**
    1. Tối ưu hóa và nâng cao độ chính xác của AI Chatbot, nghiên cứu mô hình ML lọc tin nhắn spam nâng cao.
    2. Đồng bộ hóa toàn diện dữ liệu Web Dashboard thời gian thực qua WebSockets.
    3. Triển khai và đưa Web Dashboard lên chạy trực tiếp trên Render Cloud.
    4. Mở rộng bộ Test Cases tự động (Automation testing) và Audit bảo mật chuyên sâu.
