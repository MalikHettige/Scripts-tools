cat << 'SCRIPT_EOF' > jwt_header_builder.py
import json, sys
PUBLIC_FIELDS = {"kty", "e", "kid", "n", "use", "alg"}
with open(sys.argv[1]) as f:
    key = json.load(f)
public_key = {k: v for k, v in key.items() if k in PUBLIC_FIELDS}
kid = public_key.get("kid", "<SET_KID>")
print("\n=== CLEAN PUBLIC JWK ===")
print(json.dumps(public_key, indent=4))
print("\n=== jwk HEADER ===")
print(json.dumps({"kid": kid, "typ": "JWT", "alg": "RS256", "jwk": public_key}, indent=4))
print("\n=== jku HEADER (fill URL) ===")
print(json.dumps({"kid": kid, "typ": "JWT", "alg": "RS256", "jku": "<YOUR_JWKS_URL>"}, indent=4))
print("\n=== JWKS BODY (host this) ===")
print(json.dumps({"keys": [public_key]}, indent=4))
SCRIPT_EOF
