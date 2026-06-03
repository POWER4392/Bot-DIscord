import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

REPO = "POWER4392/Bot-DIscord"

NEW_ISSUES = [
    {
        "title": "[Tuan 3] Nguyen Duc Duy: Lap trinh AI Chatbot va nghien cuu mo hinh chong Spam",
        "body": """### Nhiem vu Tuan 3 - Nguyen Duc Duy (AI/ML & Feature Integration Engineer):
- Tich hop API Gemini/GPT de xay dung chatbot AI dam thoai thong minh tren Discord.
- Nghien cuu mo hinh hoc may (Machine Learning) phat hien spam tin nhan nang cao de thay the hoac nang cap bo loc hien tai.
- Trang thai: Dang thuc hien."""
    },
    {
        "title": "[Tuan 3] Tong Xuan Nghia: Thiet ke UI/UX Web Dashboard va chuan bi noi dung thuyet trinh",
        "body": """### Nhiem vu Tuan 3 - Tong Xuan Nghia (UI/UX & Content Designer):
- Thiet ke giao dien (UI/UX) va lap trinh giao dien frontend co ban cho Web Dashboard quan tri thay the GUI CustomTkinter.
- Bien soan noi dung, kich ban chay demo thuc te va ho tro chuan bi slide thuyet trinh hoan chinh.
- Trang thai: Dang thuc hien."""
    },
    {
        "title": "[Tuan 3] Tran Duc Manh: Phat trien API backend va tich hop Gemini API",
        "body": """### Nhiem vu Tuan 3 - Tran Duc Manh (Backend Developer):
- Thiet ke va phat trien cac API endpoint o backend de ho tro Web Dashboard.
- Tich hop ket noi API Gemini/GPT o phia backend va toi uu hoa database.
- Trang thai: Dang thuc hien."""
    },
    {
        "title": "[Tuan 3] Do Hoang Long: Quan tri du an va trien khai Web Dashboard",
        "body": """### Nhiem vu Tuan 3 - Do Hoang Long (DevOps & Cloud Deployment):
- Quan tri tien do du an tuan moi, giam sat hoat dong he thong.
- Cau hinh moi truong va trien khai thu nghiem Web Dashboard len moi truong Render Cloud & Neon PostgreSQL.
- Xay dung kich ban chay demo thuc te va chuan bi video thuyet trinh du phong.
- Trang thai: Dang thuc hien."""
    },
    {
        "title": "[Tuan 3] Mai Van Viet: Kiem thu QA & Bao mat cho AI Chatbot & Web Dashboard",
        "body": """### Nhiem vu Tuan 3 - Mai Van Viet (QA & Security Engineer):
- Lap kich ban kiem thu (Test Cases) chi tiet cho tinh nang Chatbot AI dam thoai va Web Dashboard moi.
- Thuc hien kiem thu phat hien loi (QA) tren local va cloud, kiem thu bao mat cho cac API endpoint moi va dam bao an toan thong tin cau hinh.
- Trang thai: Dang thuc hien."""
    }
]

def create_issue(token, issue_data):
    url = f"https://api.github.com/repos/{REPO}/issues"
    data = json.dumps(issue_data).encode('utf-8')
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
                res_data = json.loads(response.read().decode('utf-8'))
                print(f"[+] Tao thanh cong Issue #{res_data['number']}: {issue_data['title']}")
                return True
    except Exception as e:
        print(f"[-] Loi khi tao Issue: {e}")
        return False

def main():
    print("=== TOOL TU DONG TAO GITHUB ISSUES TUAN 3 ===")
    print(f"Repository: {REPO}")
    token = input("Nhap GitHub Personal Access Token (PAT) cua ban: ").strip()
    if not token:
        print("Token khong duoc de trong!")
        return
    
    print("\nBat dau tao cac issue...")
    success_count = 0
    for issue in NEW_ISSUES:
        if create_issue(token, issue):
            success_count += 1
            
    print(f"\nHoan thanh! Da tao thanh cong {success_count}/{len(NEW_ISSUES)} issues.")

if __name__ == "__main__":
    main()
