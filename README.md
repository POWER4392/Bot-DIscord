# 🤖 Hướng Dẫn Sử Dụng Bot Discord (All-In-One Bot)

Chào mừng bạn đến với tài liệu hướng dẫn sử dụng chính thức của Bot Discord. Đây là một bot đa chức năng được thiết kế để nâng cao trải nghiệm của cộng đồng, cung cấp các công cụ từ quản lý máy chủ, giải trí âm nhạc, hệ thống kinh tế cho đến các tiện ích tùy chỉnh. 

Tài liệu này sẽ cung cấp cho bạn thông tin chi tiết về các tính năng và danh sách các lệnh để tận dụng tối đa khả năng của Bot.

---

## 🌟 TÍNH NĂNG NỔI BẬT

- **🎶 Âm Nhạc Chất Lượng Cao:** Phát nhạc trực tiếp từ YouTube, hỗ trợ hàng đợi, bỏ qua và điều khiển phát lại mượt mà.
- **💰 Hệ Thống Kinh Tế & Cấp Độ:** Tích hợp hệ thống điểm danh nhận thưởng, cửa hàng, tài xỉu, và thẻ cấp độ (Rank Card) được thiết kế đẹp mắt.
- **🛡️ Quản Lý Cấp Cao:** Cung cấp đầy đủ công cụ Moderation (Kick, Ban, Mute, Xóa tin nhắn, Lọc từ ngữ) giúp Admin quản lý máy chủ hiệu quả.
- **📡 Theo Dõi Mạng Xã Hội:** Tự động thông báo khi có bài viết hoặc video mới từ YouTube, TikTok, Reddit, Facebook.
- **🎟️ Hỗ Trợ Nhanh Chóng:** Tích hợp hệ thống Ticket giúp người dùng dễ dàng liên hệ với đội ngũ quản trị.

---

## 📖 DANH SÁCH LỆNH (COMMANDS)

*(Lưu ý: Tiền tố mặc định của bot là `!`. Quản trị viên có thể thay đổi tiền tố này thông qua Bảng điều khiển Bot).*

### 🎵 1. Lệnh Âm Nhạc & Giải Trí
Nhóm lệnh này hỗ trợ mọi thành viên trong việc điều khiển âm nhạc và kiểm tra trạng thái bot.

- `!play <Tên bài hát hoặc Link>`: Yêu cầu Bot tham gia kênh thoại và phát nhạc. Bot sẽ tự động tìm kiếm và phát bài hát.
- `!skip`: Bỏ qua bài hát hiện tại và phát bài tiếp theo trong hàng đợi.
- `!pause`: Tạm dừng bài hát đang phát.
- `!resume`: Tiếp tục phát nhạc sau khi tạm dừng.
- `!stop`: Dừng phát nhạc hoàn toàn, xóa hàng đợi và yêu cầu Bot rời khỏi kênh thoại.
- `!ping`: Kiểm tra độ trễ (latency) của Bot tới máy chủ Discord (tính bằng ms).

### 💳 2. Lệnh Hệ Thống Kinh Tế & Cấp Độ
Nhóm lệnh này giúp người dùng tham gia vào nền kinh tế của máy chủ và kiểm tra cấp bậc.

- `!daily`: Điểm danh nhận phần thưởng hàng ngày (Mặc định: 200 Vàng). Có thể sử dụng mỗi 24 giờ.
- `!bank`: Kiểm tra thông tin ví tiền, số dư hiện tại và cấp độ của bạn.
  - *Lưu ý: Lệnh này bao gồm một Mini-Shop và hệ thống minigame (Tài Xỉu) để bạn có thể kiếm thêm hoặc mua các danh hiệu (Role) đặc biệt.*
- `!rank` hoặc `!rank @Người_Dùng`: Hiển thị Thẻ Cấp Độ (Rank Card) cá nhân hoặc của người khác với giao diện được thiết kế độc quyền.

### 🎙️ 3. Lệnh Tiện Ích Cá Nhân
- `!myvoice <Tên_Kênh>`: Tự động tạo một kênh thoại riêng tư. Bạn sẽ có toàn quyền quản lý kênh này (đổi tên, mời/đuổi người khác). Kênh sẽ tự động bị xóa nếu không có người dùng nào bên trong sau 60 giây.

---

## 🛡️ DÀNH CHO QUẢN TRỊ VIÊN (MODERATOR / ADMIN)

Các lệnh dưới đây chỉ dành cho những người dùng có quyền `Administrator` hoặc các vai trò (Role) được cấp quyền quản lý trong máy chủ.

### 🚧 Cài Đặt Hệ Thống & Tự Động Hóa
- `!ticket_setup`: Khởi tạo hệ thống Hỗ trợ (Ticket) tại kênh hiện tại. Một giao diện nút bấm sẽ xuất hiện, cho phép người dùng click để tạo kênh hỗ trợ riêng tư với đội ngũ quản trị.
- `!setup_voice`: Tạo giao diện nút bấm hỗ trợ tạo kênh thoại riêng tư thay vì phải sử dụng lệnh `!myvoice`.

### ⚖️ Quản Lý & Chế Tài (Moderation)
- `!kick @Người_Dùng [Lý do]`: Trục xuất một thành viên khỏi máy chủ.
- `!ban @Người_Dùng [Lý do]`: Cấm vĩnh viễn một thành viên khỏi máy chủ.
- `!mute @Người_Dùng <Số_Phút> [Lý do]`: Cấm chat/nói chuyện (timeout) một thành viên trong khoảng thời gian nhất định.
- `!clear <Số Lượng>`: Xóa nhanh một lượng tin nhắn gần nhất trong kênh (Ví dụ: `!clear 10` sẽ xóa 10 tin nhắn).
- `!addword <Từ_Ngữ>`: Thêm một từ ngữ vào danh sách cấm. Nếu người dùng vi phạm, tin nhắn sẽ tự động bị xóa.
- `!delword <Từ_Ngữ>`: Xóa một từ khỏi danh sách cấm.

### 📡 Cấu Hình Mạng Xã Hội (Social Radar)
Hệ thống sẽ quét các nền tảng mạng xã hội mỗi 5 phút và tự động gửi thông báo khi có bài viết hoặc video mới.

- `!add_social <Nền_Tảng> <Link_Kênh> <#Kênh_Nhận_Thông_Báo> [@Tag_Vai_Trò]`: Đăng ký theo dõi một kênh mạng xã hội.
  - *Nền tảng hỗ trợ: `youtube`, `tiktok`, `reddit`, `facebook`.*
  - *Ví dụ: `!add_social youtube https://youtube.com/... #thong-bao @everyone`*
- `!rm_social <Nền_Tảng> <Link_Kênh>`: Hủy theo dõi một kênh mạng xã hội.
- `!list_social`: Hiển thị danh sách tất cả các kênh mạng xã hội đang được theo dõi trên máy chủ.

---

## 🚀 HƯỚNG DẪN KHỞI CHẠY (DÀNH CHO NGƯỜI CHẠY BOT)

Nếu bạn là người cài đặt và vận hành Bot, vui lòng làm theo các bước sau:

1. **Yêu cầu hệ thống:**
   - Cài đặt Python phiên bản mới nhất.
   - Cài đặt các thư viện cần thiết: `discord.py`, `PyNaCl`, `yt-dlp`, `customtkinter`, `Pillow`, `psutil`.
   - Cài đặt FFMPEG (Thêm vào PATH hệ thống hoặc để file `ffmpeg.exe` chung thư mục gốc).

2. **Khởi động Bot qua Giao diện điều khiển (GUI):**
   - Chạy lệnh: `python setting_gui.py` để mở bảng điều khiển.
   - Trong thẻ **Configuration**, điền **Discord Bot Token** của bạn.
   - Thiết lập các tùy chọn khác như Tiền tố lệnh (Prefix), hình ảnh Rank Card, v.v.
   - Nhấn nút **[▶ CHẠY BOT]** để khởi động.

---
*Cảm ơn bạn đã tin tưởng và sử dụng Bot. Chúc cộng đồng của bạn ngày càng phát triển vững mạnh!*
