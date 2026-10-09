I struggled coverting my copied JWK of a new RSA key into a executable format of the header section on JWT web token panel. When I have to turn a new JWK into that format i figured it would be a better idea to use an automated script.

# JWK Header Builder

A small utility that takes a full RSA JWK (as copied from Burp Suite's JWT Editor, including private key fields) and strips it down to the public-only fields, then prints ready-to-use JWT header blocks for both `jwk` header injection and `jku` header injection attacks — plus the JWKS document you need to host for the `jku` variant.

## Why this exists

When testing JWT authentication bypass via `jwk` or `jku` header injection, a common mistake is accidentally pasting the **full key object** (including private fields like `d`, `p`, `q`, `qi`, `dp`, `dq`) into the JWT header or exploit server body instead of the public-only fields. This script removes that manual step entirely.

## Requirements

- Python 3

No external libraries needed — uses only the standard library (`json`, `sys`).

## Usage

**1. Save your JWK to a file.**

Copy the key from Burp (right-click your RSA key in JWT Editor → Copy Public Key as JWK, or copy the full key dialog if that's all that's available), then create a file with it:

```bash
cat << 'EOF' > key.json
<paste your JWK JSON here>
EOF
```

**2. Run the script against that file:**

```bash
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


## Notes

- The outer `kid` and the `kid` inside the embedded `jwk` (or inside the hosted JWKS) must match — the script handles this automatically by using the same `kid` from your input key throughout all output blocks.
- When signing the forged JWT in Burp, make sure you select the **same RSA key** whose public half you embedded — signing with a different key will produce a signature that doesn't match.
- In Burp's JWT Editor, check **"Don't modify header"** when signing, otherwise Burp may silently overwrite your manually-set `jwk`/`jku` fields with its own default behavior.
- This script does not fetch, host, or send anything — it only transforms JSON locally. You still need to manually host the JWKS body (e.g. on an exploit server or static host) for the `jku` variant, and manually paste the headers into your intercepting proxy.
