# KỊCH BẢN CHẠY DEMO DỰ ÁN DISCORD BOT & WEB DASHBOARD
## Dành cho Buổi Báo cáo Môn học Công Nghệ Phần Mềm

Tài liệu này hướng dẫn chi tiết từng bước chuẩn bị và các kịch bản trình diễn thực tế trong buổi báo cáo dự án.

---

## 1. Giai đoạn chuẩn bị (Setup & Verification)
* **Bước 1:** Khởi động bot ở môi trường local hoặc cloud.
  - Lệnh khởi động local: `python main.py`
  - Đảm bảo terminal log ra: `[THONG BAO] Bot CyberBot#9999 da Started thanh cong!` và `[API] HTTP API server đang lắng nghe tại cổng 8080`.
* **Bước 2:** Mở trình duyệt và truy cập Web Dashboard bằng cách mở tệp `dashboard/index.html`.
* **Bước 3:** Nhập địa chỉ API Server (`http://localhost:8080` hoặc domain Render của nhóm) và khóa bí mật (`changeme123`) vào bảng điều khiển góc trên cùng bên phải của dashboard. Click **"Kết nối lại"** và kiểm tra trạng thái hiển thị **"Kết nối thành công"** (màu xanh lá cây).

---

## 2. Kịch bản Demo 1: AutoMod & Anti-Spam (Tính năng Bảo mật)
* **Mục tiêu:** Trình diễn khả năng tự động phát hiện và xử lý vi phạm cực nhanh của Bot.
* **Các bước thực hiện:**
  1. Sử dụng tài khoản Discord phụ (không có quyền Admin/Mod) gửi liên kết lừa đảo giả mạo vào kênh chung:
     - Gửi tin nhắn chứa: `https://free-nitro-discord.gift/claim`
     - **Kết quả:** Ngay lập tức (dưới 300ms), tin nhắn biến mất. Bot gửi một tin nhắn ẩn hoặc gửi thông báo cảnh cáo và ghi log vi phạm.
  2. Thực hiện spam tin nhắn liên tục (gửi liên tiếp 6 tin nhắn trong vòng 3 giây):
     - **Kết quả:** Các tin nhắn spam bị bot xóa hàng loạt. Tài khoản phụ lập tức bị đưa vào trạng thái **Timeout 5 phút** (không thể chat).
     - Kiểm tra kênh `#moderation-logs` bằng tài khoản Admin để thấy log báo cáo chi tiết thời gian và lý do xử lý tài khoản phụ.

---

## 3. Kịch bản Demo 2: Đàm thoại AI Chatbot (Trí tuệ nhân tạo)
* **Mục tiêu:** Trình diễn tính năng trò chuyện thông minh với Gemini 1.5 Flash.
* **Các bước thực hiện:**
  1. Truy cập vào kênh chat được cấu hình cho AI (ví dụ: `#general-chat` hoặc `#chat-ai`). Gửi một câu hỏi thông thường:
     - Chat: `Bạn có thể giới thiệu về kiến trúc phần mềm MVC không?`
     - **Kết quả:** Bot trả lời bằng tiếng Việt cực kỳ tự nhiên, trích xuất thông tin chuẩn xác từ mô hình Gemini.
  2. Đổi tính cách của Bot qua Web Dashboard:
     - Mở Web Dashboard -> Tab **"Cấu hình AI"**.
     - Đổi nội dung **System Prompt** thành:
       `Bạn là một hải tặc vui tính, thường xuyên xưng hô là "Ta" và "Ngươi", cuối mỗi câu trả lời luôn thêm cụm từ "Ahoy!".`
     - Click **"Lưu Cấu Hình AI"**.
  3. Quay lại kênh chat Discord và hỏi lại câu tương tự hoặc đặt câu hỏi mới:
     - Chat: `Hôm nay thời tiết thế nào?`
     - **Kết quả:** Bot trả lời theo đúng phong cách hải tặc: `"Ahoy! Hôm nay thời tiết trên biển rất đẹp để ra khơi..."`

---

## 4. Kịch bản Demo 3: Web Dashboard & Reaction Roles (Tương tác Quản trị)
* **Mục tiêu:** Trình diễn sự đồng bộ hóa dữ liệu thời gian thực giữa Web UI và Discord.
* **Các bước thực hiện:**
  1. Trên Web Dashboard -> Chọn tab **"Reaction Roles"**.
  2. Chọn Server và Kênh chat muốn gửi bảng (ví dụ: `#role-tự-chọn`).
  3. Điền tiêu đề: `LỰA CHỌN VAI TRÒ HỌC TẬP`
  4. Điền mô tả: `Nhấn nút bên dưới để nhận vai trò phù hợp của bạn.`
  5. Cài đặt 2 vai trò:
     - Role 1: `Member` | Mô tả: `Vai trò thành viên chính thức`
     - Role 2: `Gamer` | Mô tả: `Nhận thông báo khi chơi game`
  6. Click **"Gửi Panel Lên Server"**.
  7. Quay lại Discord, kiểm tra kênh chat tương ứng:
     - **Kết quả:** Một tin nhắn nhúng (Embed) tuyệt đẹp màu xanh dương được tạo ra với 2 nút bấm: `@Member` và `@Gamer`.
     - Người dùng click vào nút `@Member` -> Bot phản hồi: `"Đã cấp vai trò Member cho bạn!"`. Click lại lần nữa -> Bot phản hồi: `"Đã gỡ vai trò Member khỏi bạn!"`.

---

## 5. Kịch bản Demo 4: Tiện ích Giải trí (Music & Rank Card)
* **Mục tiêu:** Trình diễn các tính năng giải trí đa dạng nâng cao trải nghiệm server.
* **Các bước thực hiện:**
  1. Gõ lệnh `/rank` trong kênh bot commands.
     - **Kết quả:** Bot gửi về một Rank Card dạng ảnh tuyệt đẹp được render động bằng thư viện Pillow chứa avatar của bạn, số XP hiện tại, Level và tiến trình lên cấp.
  2. Tham gia vào một kênh thoại bất kỳ.
  3. Gõ lệnh phát nhạc: `/play query: lofi hiphop`
     - **Kết quả:** Bot tham gia kênh thoại, tải luồng âm thanh trực tiếp bằng `yt-dlp` và phát nhạc mượt mà.
     - Bot hiển thị một panel điều khiển nhạc có các nút bấm: Tạm dừng, Tiếp tục, Chuyển bài, Hiện danh sách đợi.

---

## 6. Kịch bản Demo 5: Giám sát Hệ thống trên Cloud (DevOps)
* **Mục tiêu:** Trình diễn tính thực tiễn khi đưa dự án lên sản xuất (Production Ready).
* **Các bước thực hiện:**
  1. Mở trang quản trị dịch vụ Render để chứng minh dịch vụ bot đang chạy live 24/7.
  2. Mở Neon.tech PostgreSQL dashboard chỉ ra các bảng dữ liệu thực tế đang đồng bộ hóa dữ liệu từ người dùng.
  3. Mở UptimeRobot chỉ ra biểu đồ Uptime 100% của hệ thống trong tuần qua.
