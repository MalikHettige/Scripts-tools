python3 - <<'EOF'
import base64

cookie = "Y2FybG9zOjI2MzIyZE2ZDVmNGRhYmZmM2JiMTM2ZjI0NjBhOTQz"
decoded = base64.b64decode(cookie).decode()
print(f"Decoded: {decoded}")
# Format: carlos:md5hash
# Copy the hash part and crack it at crackstation.net
EOF
