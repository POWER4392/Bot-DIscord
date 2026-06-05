# Sơ đồ Cơ sở dữ liệu (Database Schema Specification)

Hệ thống Discord Bot của Nhóm 69 hỗ trợ cấu trúc cơ sở dữ liệu kép (SQLite cho môi trường phát triển cục bộ và Neon Cloud PostgreSQL cho môi trường triển khai Production).

---

## 📊 1. Sơ đồ các bảng (Tables Schema)

### 👤 Bảng `users` (Quản lý cấp bậc & điểm tích lũy)
Lưu thông tin điểm kinh nghiệm (XP), cấp độ (Level) và số xu kinh tế của người dùng Discord.

| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `user_id` | `VARCHAR(30)` | **PRIMARY KEY** | ID người dùng Discord |
| `xp` | `INTEGER` | DEFAULT 0 | Điểm kinh nghiệm tích lũy |
| `level` | `INTEGER` | DEFAULT 1 | Cấp bậc hiện tại của thành viên |
| `coins` | `INTEGER` | DEFAULT 100 | Số xu kinh tế ảo |
| `last_message_at` | `TIMESTAMP` | | Thời điểm gửi tin nhắn cuối cùng (chống spam XP) |

---

### ⚠️ Bảng `warnings` (Theo dõi vi phạm kiểm duyệt)
Lưu trữ các cảnh báo vi phạm của thành viên khi vi phạm các quy tắc kiểm duyệt hoặc AutoMod.

| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` / `INTEGER` | **PRIMARY KEY AUTOINCREMENT** | ID tự tăng của bản ghi vi phạm |
| `user_id` | `VARCHAR(30)` | **FOREIGN KEY** (references `users`) | ID người dùng vi phạm |
| `moderator_id` | `VARCHAR(30)` | | ID người thực thi (hoặc "AutoMod") |
| `reason` | `TEXT` | | Lý do cảnh báo |
| `created_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Thời gian ghi nhận cảnh báo |

---

### ❓ Bảng `verification_quiz` (Ngân hàng câu hỏi xác minh)
Lưu trữ bộ câu hỏi trắc nghiệm dùng để xác minh thành viên khi mới gia nhập máy chủ.

| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `SERIAL` / `INTEGER` | **PRIMARY KEY AUTOINCREMENT** | ID tự tăng của câu hỏi |
| `question` | `TEXT` | NOT NULL | Nội dung câu hỏi trắc nghiệm |
| `options` | `TEXT` | NOT NULL | Các lựa chọn dạng JSON Array (ví dụ: `["A", "B", "C"]`) |
| `correct_option` | `INTEGER` | NOT NULL | Chỉ mục của câu trả lời đúng (0-indexed) |
| `created_at` | `TIMESTAMP` | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo câu hỏi |

---

### ⏳ Bảng `timed_roles` (Vai trò tự động hết hạn)
Quản lý các vai trò tạm thời được gán cho người dùng (ví dụ: Mute tạm thời).

| Trường | Kiểu dữ liệu | Ràng buộc | Mô tả |
| :--- | :--- | :--- | :--- |
| `user_id` | `VARCHAR(30)` | | ID người dùng được gán |
| `role_id` | `VARCHAR(30)` | | ID vai trò được gán |
| `expires_at` | `TIMESTAMP` | NOT NULL | Thời điểm vai trò tự động bị gỡ bỏ |
| **PRIMARY KEY** | (`user_id`, `role_id`) | | Khóa chính phức hợp |
