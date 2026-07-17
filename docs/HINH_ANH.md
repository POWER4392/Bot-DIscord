# DANH SÁCH HÌNH ẢNH SƠ ĐỒ HỆ THỐNG
## (Dành cho việc chèn báo cáo hoặc tham khảo bản vẽ độ phân giải cao)

Tài liệu này lưu trữ tất cả các hình ảnh sơ đồ thiết kế hệ thống dưới dạng tệp tin ảnh PNG. **Toàn bộ hình ảnh đã được xử lý về định dạng đơn sắc (grayscale/không màu) để phục vụ cho việc chèn vào báo cáo Word/docx môn học.**

### 1. Sơ đồ Kiến trúc Hệ thống (High-Level Architecture)
- **Tên tệp:** `architecture_diagram.png`
- **Đường dẫn tệp:** [architecture_diagram.png](file:///d:/Code/Bot/docs/images/architecture_diagram.png)
- **Mô tả:** Sơ đồ khối tổng quan 4 tầng: Web Dashboard → API Server Engine → Discord Bot Core → (Cogs Modules / Database / Gemini AI API).

---

### 2. Sơ đồ Use Case Tổng Quan
- **Tên tệp:** `usecase_diagram.png`
- **Đường dẫn tệp:** [usecase_diagram.png](file:///d:/Code/Bot/docs/images/usecase_diagram.png)
- **Mô tả:** Biểu diễn các tác nhân (Member, Admin/Mod, System Bot) và 11 ca sử dụng chính của hệ thống.

---

### 2. Sơ đồ Hoạt động (Activity Diagrams)

#### 2.1. Luồng AutoMod (Kiểm duyệt tự động)
- **Tên tệp:** `flowchart_automod.png`
- **Đường dẫn tệp:** [flowchart_automod.png](file:///d:/Code/Bot/docs/images/flowchart_automod.png)
- **Mô tả:** Quy trình phân tích tin nhắn và xử lý vi phạm thời gian thực.

#### 2.2. Luồng Phát nhạc YouTube
- **Tên tệp:** `flowchart_music.png`
- **Đường dẫn tệp:** [flowchart_music.png](file:///d:/Code/Bot/docs/images/flowchart_music.png)
- **Mô tả:** Luồng nghiệp vụ kết nối kênh thoại, trích xuất nhạc bằng yt-dlp và quản lý hàng đợi phát.

#### 2.3. Luồng AI Chatbot & Logging Token
- **Tên tệp:** `flowchart_ai_chat.png`
- **Đường dẫn tệp:** [flowchart_ai_chat.png](file:///d:/Code/Bot/docs/images/flowchart_ai_chat.png)
- **Mô tả:** Quy trình đàm thoại AI, xử lý RAG từ luật lệ server và lưu vết lịch sử, token sử dụng.

---

### 3. Sơ đồ Lớp (Class Diagram)
- **Tên tệp:** `class_diagram_cog.png`
- **Đường dẫn tệp:** [class_diagram_cog.png](file:///d:/Code/Bot/docs/images/class_diagram_cog.png)
- **Mô tả:** Cấu trúc lớp của các plugin Cog và các View tương tác trên Discord.

---

### 4. Sơ đồ Tuần tự (Sequence Diagram)
- **Tên tệp:** `sequence_diagram_play.png`
- **Đường dẫn tệp:** [sequence_diagram_play.png](file:///d:/Code/Bot/docs/images/sequence_diagram_play.png)
- **Mô tả:** Sự tương tác giữa người dùng, Bot Core, Music Cog, yt-dlp và FFmpeg khi phát nhạc.

---

### 5. Sơ đồ Quan hệ Thực thể Cơ sở Dữ liệu (ERD)
- **Tên tệp:** `erd_diagram.png`
- **Đường dẫn tệp:** [erd_diagram.png](file:///d:/Code/Bot/docs/images/erd_diagram.png)
- **Mô tả:** Sơ đồ quan hệ thực thể tổng quát liên kết thực thể trung tâm `guilds` và `users` với toàn bộ các thực thể bảng dữ liệu khác.

---
*Các tệp hình ảnh đơn sắc được lưu trữ trực tiếp trong thư mục `/docs/images` của dự án.*
