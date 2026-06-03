import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

REPO = "POWER4392/Bot-DIscord"

def fetch_url(url, token):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Python-urllib"
        }
    )
    with urllib.request.urlopen(req, context=ctx) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    token = input("Nhap GitHub PAT: ").strip()
    try:
        user_info = fetch_url("https://api.github.com/user", token)
        print(f"[+] Token owner: {user_info.get('login')}")
    except Exception as e:
        print(f"[-] Loi khi lay thong tin user: {e}")
        return

    try:
        issues = fetch_url(f"https://api.github.com/repos/{REPO}/issues", token)
        print(f"[+] Tim thay {len(issues)} issues dang mo:")
        for issue in issues:
            print(f"  - Issue #{issue['number']} (State: {issue['state']})")
    except Exception as e:
        print(f"[-] Loi khi lay danh sach issues: {e}")

if __name__ == "__main__":
    main()
