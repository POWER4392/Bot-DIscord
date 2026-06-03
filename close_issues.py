import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

REPO = "POWER4392/Bot-DIscord"
ISSUE_NUMS = [1, 2, 3, 4, 5]

def close_issue(token, issue_num):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}"
    data = json.dumps({"state": "closed"}).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Python-urllib"
        },
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status == 200:
                print(f"[+] Dong thanh cong Issue #{issue_num}")
                return True
    except Exception as e:
        print(f"[-] Loi khi dong Issue #{issue_num}: {e}")
        return False

def main():
    print("=== TOOL TU DONG DONG GITHUB ISSUES ===")
    print(f"Repository: {REPO}")
    token = input("Nhap GitHub Personal Access Token (PAT) cua ban: ").strip()
    if not token:
        print("Token khong duoc de trong!")
        return
    
    print("\nBat dau dong cac issue...")
    success_count = 0
    for issue_num in ISSUE_NUMS:
        if close_issue(token, issue_num):
            success_count += 1
            
    print(f"\nHoan thanh! Da dong thanh cong {success_count}/{len(ISSUE_NUMS)} issues.")

if __name__ == "__main__":
    main()
