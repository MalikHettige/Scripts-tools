# JWK Header Builder

A small utility that takes a full RSA JWK (as copied from Burp Suite's JWT Editor, including private key fields) and strips it down to the public-only fields, then prints ready-to-use JWT header blocks for both `jwk` header injection and `jku` header injection attacks — plus the JWKS document you need to host for the `jku` variant.

## Why this exists

When testing JWT authentication bypass via `jwk` or `jku` header injection, a common mistake is accidentally pasting the **full key object** (including private fields like `d`, `p`, `q`, `qi`, `dp`, `dq`) into the JWT header or exploit server body instead of the public-only fields. This script removes that manual step entirely. Choosing an AI for this is also a good choice but I don't think sharing a sensitive crafted public/private key of a real world website is the best approach.

## Requirements

- Python 3
No external libraries needed — uses only the standard library (`json`, `sys`).

## Option A

Clone the repo and run directly — the script is already there, no setup needed:
```bash
git clone https://github.com/MalikHettige/Scripts-tools.git
cd Scripts-tools/JWT/jwk-jku-header-builder
```
And paste this block (replace the 2nd line with the JWK)
```
cat << 'EOF' > key.json
<paste your JWK JSON here>
EOF
python3 jwt_header_builder.py key.json
```

## Option B (no cloning needed, just create the file and execute)
**1. Save your JWK to a file.**
Run the script and confirm the file is created by running 
```bash
ls -la key.json
```
The result would be something like :
```-rw-r--r-- 1 malik 197609 1723 Oct  9 15:34 key.json```

**That confirms it worked correctly:**

```-rw-r--r--``` → normal readable/writable file
```key.json``` → correct filename

**2. Run the script against that file:**
Paste this block, don't forget to replace ```<paste JWK>``` with your JWK (right-click your RSA key in JWT Editor → Copy Public Key as JWK,)

```bash
cat << 'EOF' > key.json
<paste JWK>
EOF
python3 jwt_header_builder.py key.json
```

## Output
The script prints four blocks:

1. **Clean public JWK** — only `kty`, `e`, `kid`, `n` (and `use`/`alg` if present) — all private key material stripped out
2. **`jwk` header** — a ready JWT header with the public key embedded inline, for `jwk` header injection
3. **`jku` header** — a ready JWT header with a placeholder URL, for `jku` header injection (replace `<YOUR_JWKS_URL>` with your hosted endpoint)
4. **JWKS body** — the `{"keys": [...]}` document to host at your `jku` URL

Paste the relevant block directly into Burp's JWT Editor header field (for `jwk`/`jku` injection) or your exploit server's response body (for the JWKS document).

## Example

<img width="1919" height="805" alt="image" src="https://github.com/user-attachments/assets/b4f2b6e6-c607-4365-a571-4aa6322e6e41" />

## Notes

- The outer `kid` and the `kid` inside the embedded `jwk` (or inside the hosted JWKS) must match — the script handles this automatically by using the same `kid` from your input key throughout all output blocks.
- When signing the forged JWT in Burp, make sure you select the **same RSA key** whose public half you embedded — signing with a different key will produce a signature that doesn't match.
- In Burp's JWT Editor, check **"Don't modify header"** when signing, otherwise Burp may silently overwrite your manually-set `jwk`/`jku` fields with its own default behavior.
- This script does not fetch, host, or send anything — it only transforms JSON locally. You still need to manually host the JWKS body (e.g. on an exploit server or static host) for the `jku` variant, and manually paste the headers into your intercepting proxy.
