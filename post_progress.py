import urllib.request
import json
import ssl

# Disable SSL verification for convenience if needed, but standard is fine
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

REPO = "POWER4392/Bot-DIscord"
ISSUES = {
    1: """### Tiến độ công việc Tuần 2:
- **Thiết kế kiến trúc Bot:** Đã hoàn thành cấu trúc cốt lõi (`main.py`, Command & Event Handler).
- **Lập trình các tính năng chính:** Moderation, Utilities, Music Player (phát nhạc YouTube bằng yt-dlp).
- **Cơ sở dữ liệu:** Xây dựng lớp trừu tượng cơ sở dữ liệu (`core/database.py` hỗ trợ SQLite & PostgreSQL).
- **Kết nối liên tiến trình (IPC):** Thiết lập HTTP API Server để GUI Desktop có thể cấu hình bot.
- **Trạng thái:** Hoàn thành 100% đúng tiến độ.""",
    
    2: """### Tiến độ công việc Tuần 2:
- **Thuật toán AutoMod nâng cao:** Đã hoàn thành Regex phát hiện link Phishing/Scam và thuật toán Sliding Window chống spam (>5 tin/3.5s).
- **Tính năng Social Crawler:** Tự động theo dõi và cập nhật RSS từ YouTube, Reddit, TikTok (`cogs/social.py`).
- **Hệ thống Kinh tế & Cấp độ:** Lập trình hệ thống XP, Leveling và thuật toán Gamification (`cogs/economy.py`).
- **Trạng thái:** Hoàn thành 100% đúng tiến độ.""",
    
    3: """### Tiến độ công việc Tuần 2:
- **Quản lý dự án:** Điều phối tiến độ, phân chia công việc cho 5 thành viên.
- **Triển khai ứng dụng Cloud:** Deploy bot thành công lên Render Cloud Hosting chạy 24/7.
- **Quản lý Database:** Cấu hình và đồng bộ cơ sở dữ liệu Neon Serverless PostgreSQL trên đám mây.
- **Giám sát & Tài liệu:** Thiết lập UptimeRobot để ping giám sát Uptime 24/7, biên soạn tệp báo cáo môn học (`BAO_CAO_CNPM.md`) và slide thuyết trình (`slides.txt`).
- **Trạng thái:** Hoàn thành 100% đúng tiến độ.""",
    
    4: """### Tiến độ công việc Tuần 2:
- **Kịch bản kiểm thử:** Xây dựng bộ tài liệu kịch bản kiểm thử (Test Cases) chi tiết cho từng tính năng của bot.
- **Chạy kiểm thử:** Thực hiện test thực tế trên cả môi trường local và cloud (Black-box & White-box testing) để phát hiện và ghi nhận nhật ký lỗi (Bug logs).
- **Bảo mật & Cấu hình:** Quản lý an toàn file môi trường `.env`, cung cấp file mẫu `config.example.json` và kiểm thử chịu tải (chống spam, chống nuke).
- **Trạng thái:** Hoàn thành 100% đúng tiến độ.""",
    
    5: """### Tiến độ công việc Tuần 2:
- **Thiết kế Giao diện Desktop GUI:** Hoàn thiện giao diện cấu hình Desktop (`setting_gui.py`) bằng `customtkinter`.
- **Giao diện hiển thị Discord (Embeds/Buttons):** Thiết kế định dạng tin nhắn nhúng, các nút bấm (Buttons), menu lựa chọn thân thiện với người dùng.
- **Phác thảo Web Dashboard:** Lập phương án thiết kế giao diện quản trị Web Dashboard thay thế GUI CustomTkinter.
- **Trạng thái:** Hoàn thành 100% đúng tiến độ."""
}

def post_comment(token, issue_num, body):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}/comments"
    data = json.dumps({"body": body}).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Python-urllib"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status == 201:
                print(f"[+] Đăng thành công cho Issue #{issue_num}")
                return True
    except Exception as e:
        print(f"[-] Lỗi khi đăng cho Issue #{issue_num}: {e}")
        return False

def main():
    print("=== TOOL TỰ ĐỘNG ĐĂNG TIẾN ĐỘ TUẦN 2 LÊN GITHUB ISSUES ===")
    print(f"Repository: {REPO}")
    token = input("Nhập GitHub Personal Access Token (PAT) của bạn: ").strip()
    if not token:
        print("Token không được để trống!")
        return
    
    print("\nBắt đầu đăng bình luận...")
    success_count = 0
    for issue_num, body in ISSUES.items():
        if post_comment(token, issue_num, body):
            success_count += 1
            
    print(f"\nHoàn thành! Đã đăng thành công {success_count}/{len(ISSUES)} issues.")

if __name__ == "__main__":
    main()
