
# JWT authentication bypass via algorithm confusion

Forges an HS256-signed JWT by using a target's RSA **public** key (PEM file) as the HMAC secret — exploits servers that trust the `alg` header to decide verification mode instead of enforcing one algorithm server-side.

## forge_token.py
python3 forge_token.py <public_key.pem>
Edit the placeholder values in the script before running:
- `TARGET_KID_VALUE` — the `kid` the server expects (if any)
- `TARGET_ISSUER` — the `iss` claim the server checks
- `TARGET_USERNAME` — the `sub` you're forging as (e.g. `administrator`)

Prints a complete forged JWT to stdout. The PEM file must be the **exact byte-for-byte** public key the server uses for RS256 verification — line endings and whitespace matter, since HMAC treats the file as raw bytes.

### Where to get the target's public key
- `/jwks.json` or `/.well-known/jwks.json`
- OIDC discovery document
- Embedded TLS certificate
- Any endpoint that legitimately exposes it for RS256 verification by other services

### Notes
- `exp` is hardcoded far in the future (`9999999999`) — adjust if the target validates sane expiry windows.
- This only works if the server's JWT library allows both RS256 and HS256 in the same algorithm allowlist — confirm that's plausible before spending time here (see your JWT doc, Part 7/8).
