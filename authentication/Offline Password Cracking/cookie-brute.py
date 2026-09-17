python3 - <<'EOF'
import base64
import hashlib

cookie = "COOKIE"

# Add padding if needed
padding = 4 - len(cookie) % 4
if padding != 4:
    cookie += "=" * padding

decoded = base64.b64decode(cookie).decode()
print(f"Decoded: {decoded}")

# Extract the hash
parts = decoded.split(":")
if len(parts) == 2:
    username, md5hash = parts
    print(f"Username: {username}")
    print(f"MD5 hash: {md5hash}")
    print(f"\nNow go to crackstation.net and paste this hash:")
    print(md5hash)
EOF
