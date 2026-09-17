python3 - <<'EOF'
import requests
import base64

base_url = "URL"

# Step 1 — Log in as wiener with stay-logged-in
r = requests.post(
    f"{base_url}/login",
    data={"username": "wiener", "password": "peter", "stay-logged-in": "on"},
    allow_redirects=False
)

cookie = r.cookies.get("stay-logged-in")
print(f"Raw cookie: {cookie}")

# Step 2 — Decode it
try:
    decoded = base64.b64decode(cookie).decode()
    print(f"Decoded: {decoded}")
except:
    print("Not base64 — different encoding")
EOF
