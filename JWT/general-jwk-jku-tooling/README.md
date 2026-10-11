# shared-tools

General-purpose JWT utilities, not tied to any single lab or program. Each tool here is meant to be reused across engagements.

## jwtgen.py

Interactive generator for `jwk` and `jku` header injection attacks. Takes a **public** JWK (e.g. copied from Burp's JWT Editor via "Copy Public Key as JWK") and produces, in one pass:

- A cleaned public JWK (private fields stripped, only `kty`, `e`, `kid`, `n`, `use`, `alg`, `crv`, `x`, `y` kept)
- A `jwk` header block (embedded-key injection — needs no hosting)
- A `jku` header block (hosted-key injection — needs a URL)
- A JWKS body ready to host at that URL

It does **not** sign tokens, host anything, or make network requests — it only builds the JSON blocks you paste into Burp's JWT Editor (or wherever you're editing the token) and the body you host separately.

## Requirements

- Python 3
- No external packages — pure standard library (`json`, `sys`, `uuid`).

## Just want one result? (no repo, no setup)

```bash
curl -o jwtgen.py "https://raw.githubusercontent.com/MalikHettige/scripts-tools/main/JWT/general-jwk-jku-tooling/jwtgen.py"
python3 jwtgen.py
```

Delete `jwtgen.py` afterward if you don't need it again.

## Frequent use (clone and keep)

```bash
git clone https://github.com/MalikHettige/scripts-tools.git "$HOME/Documents/GitHub/Scripts-tools"
```

Then, from anywhere:

```bash
python3 "$HOME/Documents/GitHub/Scripts-tools/JWT/general-jwk-jku-tooling/jwtgen.py"
```

If you want a shorter command for repeat use, add your own alias in `~/.bashrc` (this is a personal convenience, not something the script requires):

```bash
alias jwtgen="python3 \"$HOME/Documents/GitHub/Scripts-tools/JWT/general-jwk-jku-tooling/jwtgen.py\""
```

## Usage

Run the script, then:

1. **Paste the public JWK JSON** when prompted, then press Enter on an empty line to submit it. Pressing Enter immediately with nothing pasted exits the script — it doesn't re-prompt.
2. If the pasted key has no `kid`, one is generated automatically (a random UUID) and reused consistently across every output block.
3. **Hosting URL for `jku`** — enter the URL where you plan to host the JWKS body, or press Enter to skip (useful if you're only testing `jwk` injection).
4. **Separate JWKS URL** — press Enter to reuse the URL above, or give a different one if the token's `jku` URL and the actual hosted file live at different addresses.
5. The script prints the clean public JWK, the `jwk` header block, the `jku` header block, the JWKS body to host, and (if a URL was given) the full `jku` URL for reference.

### Example

```
$ python3 jwtgen.py
=== JWT Hunter Toolkit ===

Paste the public JWK JSON (from Burp's 'Copy Public Key as JWK'):
(paste it, then press Enter on an empty line to finish — or just press Enter to skip)
{"kty": "RSA", "e": "AQAB", "n": "m0UATz...w"}

No kid found in the pasted key — generated one: e4b12e9b-8884-4161-ae55-692bc6469652

Hosting URL for jku (press Enter to skip): https://example.com/jwks.json
Separate URL for the JWKS endpoint, if different (press Enter to reuse the above):

==================================================
jwk HEADER (embedded key injection)
==================================================
{
    "kid": "e4b12e9b-8884-4161-ae55-692bc6469652",
    "typ": "JWT",
    "alg": "RS256",
    "jwk": { "kty": "RSA", "e": "AQAB", "n": "m0UATz...w", "kid": "e4b12e9b-..." }
}
...
Done.
```

## Notes

- Never paste a **private** JWK here — only the public half (`kty`, `e`, `kid`, `n`) should ever be pasted into this tool or hosted anywhere. The script strips non-public fields from its output regardless, but don't rely on that if you're worried about what you pasted in the first place — avoid pasting private key material into any tool.
- Not for algorithm confusion attacks (RS256→HS256) — that needs byte-exact PEM handling, which Burp's JWT Editor does correctly; this script covers `jwk`/`jku` injection only.
- After getting the `jwk` header block, you still need to sign the token yourself (e.g. in Burp's JWT Editor, using the private key matching the public key you pasted in) — this script only builds the header JSON, it doesn't touch signatures.
