# Giao diện & Nguyên lý Thiết kế (Design System & Guidelines)

Tài liệu này định hình phong cách thiết kế giao diện (UI/UX) cho cả **Web Dashboard** và các **Cogs Discord** thuộc hệ thống quản lý của Nhóm 69.

---

## 🌌 1. Phong cách Web Dashboard: Dark Glassmorphism

Web Dashboard được thiết kế theo trường phái **Glassmorphism (Kính mờ)** kết hợp trên nền tối (Dark mode) sang trọng, tạo cảm giác hiện đại và cao cấp.

### 🎨 Bảng màu chủ đạo (Color Palette)
- **Background chính**: Nền tối sâu lắng với hiệu ứng Radial Gradient:
  - Bắt đầu từ `#0d1117` chuyển sang `#161b22`
- **Màu kính mờ (Glass color)**: Thẻ card sử dụng màu nền mờ đục với độ trong suốt cao:
  - Nền: `rgba(255, 255, 255, 0.03)` hoặc `rgba(22, 27, 34, 0.7)`
  - Viền: `rgba(255, 255, 255, 0.08)` hoặc `rgba(139, 92, 246, 0.15)` (tím nhạt)
- **Hiệu ứng Backdrop Blur**: Cố định ở `backdrop-filter: blur(16px); webkit-backdrop-filter: blur(16px);`
- **Màu nhấn (Accent colors)**:
  - **Tím hoàng gia (Primary)**: `#8b5cf6` (tượng trưng cho công nghệ và AI)
  - **Xanh dương neon (Info)**: `#3b82f6` (tượng trưng cho dữ liệu & APIs)
  - **Xanh lá tươi (Success)**: `#10b981` (kết nối thành công / hoạt động)
  - **Cam neon (Warning)**: `#f59e0b` (các cài đặt tạm ngưng hoặc cảnh báo)

### 🔤 Kiểu chữ (Typography)
- Sử dụng Google Font **Inter** hoặc **Outfit** để đảm bảo khả năng hiển thị rõ nét trên mọi loại màn hình.
- Độ tương phản chữ được phân chia rõ:
  - Chữ chính (Primary text): `#f3f4f6` (Độ sáng 95%)
  - Chữ phụ (Secondary text): `#9ca3af` (Độ sáng 65%)

### 🌀 Hiệu ứng & Chuyển động (Micro-animations)
- Các nút tương tác (Buttons/Cards) có hiệu ứng `transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);`.
- Hover trạng thái: Tăng độ sáng viền và phóng to nhẹ `scale(1.02)`.

---

## 🤖 2. Phong cách Discord Embeds

Các thông điệp phản hồi từ Discord Bot phải đồng bộ thẩm mỹ chuyên nghiệp bằng cách sử dụng **Embeds**.

### 📐 Quy chuẩn Embeds
- **Màu sắc thanh bên (Sidebar color)**:
  - Lệnh quản trị (Moderation): `#e01a59` (Đỏ hồng)
  - chatbot AI (Gemini): `#2d8cf0` (Xanh dương)
  - Nhạc (Music): `#19be6b` (Xanh lá)
- **Cấu trúc Embed**:
  - Luôn có tiêu đề và mô tả rõ ràng.
  - Sử dụng các biểu tượng Emoji phù hợp ở đầu dòng để tăng tính sinh động.
  - Footer luôn có Timestamp và logo của Bot đại diện Nhóm 69.
