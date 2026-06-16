# Bảng Use Case & Đặc Tả: Discord Bot Quản Lý Server Tích Hợp AI

Tài liệu này cung cấp cái nhìn tổng quan về các Use Case của hệ thống, sơ đồ tương tác và bảng đặc tả chi tiết (Use Case Specification) cho các chức năng cốt lõi.

---

## 1. Danh sách Tác nhân (Actors)
- **Member (Thành viên):** Người dùng thông thường trong server, sử dụng các tiện ích của bot.
- **Moderator / Admin (Quản trị viên):** Người có quyền quản lý, thiết lập bot và kiểm duyệt nội dung.
- **System / Bot (Hệ thống):** Tiến trình xử lý tự động của bot chạy ngầm (AutoMod, Auto Tracker).

---

## 2. Danh sách Use Case Tổng Hợp

| ID | Tên Use Case | Tác nhân chính | Mô tả tóm tắt |
|----|-------------|----------------|---------------|
| **UC01** | Tự động kiểm duyệt (AutoMod) | System | Tự động quét tin nhắn phát hiện Phishing/Scam, Blacklist và spam. |
| **UC02** | Bảo vệ Server (Anti-Nuke) | System | Tự động phát hiện và ngăn chặn hành vi xóa kênh/role hàng loạt. |
| **UC03** | Quản lý Thành viên | Admin | Sử dụng lệnh Kick, Ban, Mute, Unban, Warn xử lý vi phạm. |
| **UC04** | Tạo và Quản lý Ticket | Member | Tạo kênh hỗ trợ riêng tư với Admin (Ticket). |
| **UC05** | Tạo kênh Voice tạm thời | Member | Tương tác để tạo kênh thoại tạm thời (tự xóa khi trống). |
| **UC06** | Tự cấp vai trò (Reaction Roles)| Member | Nhấn nút trên Panel để tự động nhận hoặc gỡ Role. |
| **UC07** | Phát nhạc YouTube | Member | Yêu cầu Bot phát nhạc, dừng, chuyển bài hoặc xem hàng đợi. |
| **UC08** | Hệ thống Kinh tế & Cấp độ | Member | Nhận XP, thăng cấp, nhận điểm danh hằng ngày. |
| **UC09** | Theo dõi Mạng Xã Hội | System | Tự động lấy tin tức từ YouTube, TikTok, Reddit gửi vào kênh. |
| **UC10** | Chatbot AI đàm thoại | Member | Trò chuyện tự nhiên với Bot thông qua API Gemini/GPT. |
| **UC11** | Cấu hình Bot (GUI/Web) | Admin | Sử dụng giao diện Desktop/Web để điều chỉnh thiết lập bot. |

---

## 3. Sơ đồ Use Case

```mermaid
usecaseDiagram
    actor "Member" as user
    actor "Admin/Mod" as admin
    actor "System (Bot)" as bot

    %% Member Use Cases
    user --> (Tạo và Quản lý Ticket)
    user --> (Phát nhạc YouTube)
    user --> (Chatbot AI đàm thoại)
    user --> (Tạo kênh Voice tạm thời)

    %% Admin Use Cases
    admin --> (Quản lý Thành viên)
    admin --> (Cấu hình Bot GUI/Web)
    
    %% System Use Cases
    bot --> (Tự động kiểm duyệt - AutoMod)
    bot --> (Bảo vệ Server - Anti-Nuke)

    %% Relationships
    (Quản lý Thành viên) .> (Tự động kiểm duyệt - AutoMod) : include
```

---

## 4. Đặc tả Use Case Chi Tiết (Use Case Specifications)

Dưới đây là đặc tả cho các chức năng cốt lõi nhất của hệ thống.

### 4.1. Đặc tả UC01: Tự động kiểm duyệt (AutoMod)
| Thuộc tính | Chi tiết |
|------------|----------|
| **Tên Use Case** | Tự động kiểm duyệt (AutoMod) |
| **Tác nhân** | System (Hệ thống) |
| **Mô tả** | Hệ thống tự động phân tích mọi tin nhắn gửi lên Server để phát hiện spam, từ khóa cấm (blacklist) hoặc link lừa đảo (phishing), sau đó xử lý vi phạm. |
| **Tiền điều kiện** | Bot đã được cấp quyền "Manage Messages" và "Timeout Members". Module AutoMod đã được bật. |
| **Hậu điều kiện** | Tin nhắn vi phạm bị xóa. Người dùng vi phạm bị cảnh cáo hoặc bị Timeout/Ban tùy mức độ. |
| **Luồng sự kiện chính** | 1. Member gửi một tin nhắn vào kênh chat.<br>2. System bắt sự kiện `on_message` và bỏ qua nếu là tin nhắn của Bot/Admin.<br>3. System kiểm tra tin nhắn bằng biểu thức chính quy (Regex) để tìm link Scam.<br>4. System kiểm tra từ khóa trong Blacklist.<br>5. System kiểm tra tần suất gửi tin nhắn (thuật toán Sliding Window Anti-spam).<br>6. Tin nhắn hợp lệ, System cho phép hiển thị bình thường. |
| **Luồng ngoại lệ** | - **3a. Phát hiện link Scam:** System lập tức xóa tin nhắn, Timeout người dùng 1 giờ và ghi Log.<br>- **4a. Phát hiện từ khóa cấm:** System xóa tin nhắn, cảnh cáo (Warn) người dùng và ghi Log.<br>- **5a. Phát hiện Spam (>5 tin/3.5s):** System xóa các tin nhắn spam, Timeout người dùng 5 phút và ghi Log. |

---

### 4.2. Đặc tả UC04: Tạo và Quản lý Ticket
| Thuộc tính | Chi tiết |
|------------|----------|
| **Tên Use Case** | Tạo và Quản lý Ticket |
| **Tác nhân** | Member (Chính), Admin (Phụ) |
| **Mô tả** | Cho phép người dùng mở một kênh chat riêng tư với Ban quản trị để yêu cầu hỗ trợ. |
| **Tiền điều kiện** | Bot đã khởi tạo Ticket Panel (nút bấm) tại kênh hỗ trợ. Bot có quyền tạo kênh mới (Manage Channels). |
| **Hậu điều kiện** | Một kênh văn bản riêng tư được tạo ra chỉ cho Member đó và Admin thấy. |
| **Luồng sự kiện chính** | 1. Member nhấn nút "Tạo Ticket" trên Ticket Panel.<br>2. System kiểm tra Member đã có Ticket mở nào chưa.<br>3. System tạo một kênh văn bản mới với tên `ticket-<tên-user>`.<br>4. System cấp quyền đọc/nhắn tin tại kênh đó cho Member và Admin, ẩn với mọi người khác.<br>5. System gửi một tin nhắn chào mừng và tag Admin vào kênh Ticket.<br>6. Member và Admin trao đổi. Sau khi giải quyết, Admin nhấn nút "Đóng Ticket".<br>7. System xóa kênh Ticket (hoặc lưu trữ). |
| **Luồng ngoại lệ** | - **2a. Member đã có Ticket mở:** System gửi thông báo lỗi "Bạn đã có một Ticket đang mở", hủy thao tác tạo kênh mới. |

---

### 4.3. Đặc tả UC07: Phát nhạc YouTube
| Thuộc tính | Chi tiết |
|------------|----------|
| **Tên Use Case** | Phát nhạc YouTube |
| **Tác nhân** | Member |
| **Mô tả** | Người dùng yêu cầu Bot tham gia kênh thoại và phát nhạc từ YouTube thông qua từ khóa hoặc link. |
| **Tiền điều kiện** | Member đang ở trong một kênh thoại (Voice Channel). Bot có quyền Connect và Speak. |
| **Hậu điều kiện** | Bot tham gia kênh thoại và bắt đầu phát nhạc. Kênh chat xuất hiện bảng điều khiển nhạc. |
| **Luồng sự kiện chính** | 1. Member gõ lệnh `/play <từ khóa/link>`.<br>2. System kiểm tra Member đang ở trong Voice Channel.<br>3. Bot kết nối vào Voice Channel của Member.<br>4. System sử dụng yt-dlp tải luồng âm thanh từ YouTube dựa trên truy vấn.<br>5. System đưa bài hát vào hàng đợi (Queue).<br>6. Nếu Bot đang không phát nhạc, System bắt đầu phát bài hát đầu tiên.<br>7. System gửi Panel điều khiển (Play/Pause, Skip, Stop) vào kênh chat. |
| **Luồng ngoại lệ** | - **2a. Member không ở trong Voice:** System báo lỗi "Bạn phải vào kênh thoại trước" và kết thúc.<br>- **4a. Không tìm thấy nhạc/Lỗi mạng:** System báo lỗi không tìm thấy bài hát và hủy yêu cầu. |

---

### 4.4. Đặc tả UC10: Chatbot AI đàm thoại (Gemini/GPT)
| Thuộc tính | Chi tiết |
|------------|----------|
| **Tên Use Case** | Chatbot AI đàm thoại |
| **Tác nhân** | Member |
| **Mô tả** | Người dùng hỏi đáp, trò chuyện với Bot AI thông minh qua lệnh chat. |
| **Tiền điều kiện** | API Key của Gemini/GPT đã được cấu hình hợp lệ trong `.env`. Bot có kết nối Internet ổn định. |
| **Hậu điều kiện** | Bot phản hồi câu hỏi của Member bằng ngôn ngữ tự nhiên. |
| **Luồng sự kiện chính** | 1. Member gõ lệnh `/chat <nội dung>` hoặc ping trực tiếp `@Bot <nội dung>`.<br>2. System tiếp nhận yêu cầu và hiển thị trạng thái "Đang gõ..." (Typing).<br>3. System gửi nội dung (kèm theo lịch sử ngữ cảnh nếu có) tới API của Google Gemini/OpenAI.<br>4. API xử lý và trả về đoạn text phản hồi.<br>5. System định dạng lại text (cắt nhỏ nếu quá 2000 ký tự) và gửi phản hồi lại cho Member. |
| **Luồng ngoại lệ** | - **4a. API lỗi hoặc hết hạn ngạch (Quota):** System thông báo "Hệ thống AI đang quá tải hoặc gặp sự cố, vui lòng thử lại sau". |

---

### 4.5. Đặc tả UC11: Cấu hình Bot qua Web Dashboard
| Thuộc tính | Chi tiết |
|------------|----------|
| **Tên Use Case** | Cấu hình Bot qua Web Dashboard |
| **Tác nhân** | Admin |
| **Mô tả** | Admin đăng nhập vào giao diện Web để bật/tắt tính năng, chỉnh sửa tiền tố (prefix), và xem chỉ số hệ thống. |
| **Tiền điều kiện** | Web Dashboard backend (API) đang chạy bình thường. Admin có mật khẩu đăng nhập hợp lệ. |
| **Hậu điều kiện** | Cấu hình của Bot được cập nhật theo thời gian thực mà không cần khởi động lại. |
| **Luồng sự kiện chính** | 1. Admin truy cập đường dẫn Web Dashboard.<br>2. Admin nhập mật khẩu/xác thực.<br>3. Web gọi API lấy trạng thái và cấu hình hiện tại của Bot.<br>4. Admin thay đổi một thiết lập (Ví dụ: Đổi Prefix thành `?`).<br>5. Admin nhấn "Lưu".<br>6. Web gửi request cập nhật tới backend của Bot.<br>7. Bot áp dụng cấu hình mới ngay lập tức và lưu vào `config.json` hoặc Database. |
| **Luồng ngoại lệ** | - **2a. Sai mật khẩu:** Hệ thống từ chối truy cập.<br>- **6a. Mất kết nối IPC:** Web báo lỗi không thể lưu cấu hình, yêu cầu kiểm tra lại backend. |
