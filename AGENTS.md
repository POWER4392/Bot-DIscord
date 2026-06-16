# Tài liệu Hướng dẫn Cộng tác Phát triển (AGENTS.md)

Tài liệu này cung cấp hướng dẫn lập trình, tiêu chuẩn viết code và cách cộng tác phát triển hệ thống Discord Bot cho các lập trình viên hoặc AI Agents tham gia dự án.

---

## 🛠️ 1. Quy chuẩn Lập trình (Coding Standards)

### 🐍 Quy tắc Viết Python (PEP 8)
- Sử dụng **4 khoảng trắng (spaces)** làm thụt lề thụt đầu dòng (indents), KHÔNG dùng Tabs.
- Tên biến, tên hàm viết theo kiểu `snake_case` (ví dụ: `get_user_stats`).
- Tên class viết theo kiểu `PascalCase` (ví dụ: `MusicPlayer`).
- Đóng gói logic nghiệp vụ theo **Cogs** (plugins) riêng biệt bên trong thư mục `cogs/`.

### ⚡ Xử lý Bất đồng bộ (Asyncio)
- Discord Bot vận hành hoàn toàn bất đồng bộ. Sử dụng `await` khi tương tác với mạng, database hoặc API Discord.
- Tránh các tác vụ blocking đồng bộ dài hạn (như đọc/ghi đĩa dung lượng lớn, gọi API đồng bộ). Nếu bắt buộc, hãy chạy chúng trong một luồng riêng (`asyncio.to_thread` hoặc executor).

### 🛡️ Bảo mật Thông tin Nhạy cảm
- **Mật đối tuyệt đối**: KHÔNG bao giờ commit token Discord, API keys (Gemini), mật khẩu database lên GitHub.
- Tất cả các khóa bảo mật phải được lưu trong file cấu hình `.env` cục bộ và nạp qua thư viện `python-dotenv`.
- Thêm các file nhạy cảm (`.env`, `config.json`, `cookies.txt`) vào `.gitignore`.

---

## 📈 2. Quy trình Cộng tác Git & Pull Request

### 🌿 Phân chia Nhánh (Branching Model)
- Nhánh `main`: Nhánh ổn định cao nhất, chỉ chứa code đã hoàn thiện và chạy thử thành công trên Render Cloud.
- Nhánh `develop`: Nhánh tích hợp tính năng mới. Các thành viên tạo nhánh con từ đây.
- Nhánh `feature/<issue-number>-<task-name>`: Nhánh làm việc cho từng Task cụ thể (ví dụ: `feature/23-gemini-chatbot`).

### 📦 Commit & Pull Request
- Đặt tên Commit rõ nghĩa: `feat: add AI chat`, `fix: music timeout error`, `docs: update deployment guide`.
- Khi nộp bài hoặc tạo Pull Request, hãy ghi rõ mã Issue liên kết để tự động đóng khi merge: `Closes #12` hoặc `Closes #15`.
- Khi đóng hoặc hoàn thành Task, lập trình viên cần bình luận tóm tắt kết quả kiểm thử (Logs / Screenshots) làm minh chứng.
