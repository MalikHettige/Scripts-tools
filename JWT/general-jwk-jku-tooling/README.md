
# shared-tools

General-purpose JWT utilities, not tied to any single lab or program. Each tool here is meant to be reused across engagements.

## jwtgen.py

Interactive generator for JWT key-confusion and injection attacks (`jwk` and `jku` header injection). Takes a public JWK (e.g. copied from Burp's JWT Editor via "Copy Public Key as JWK") and produces:

- A cleaned public JWK (private fields stripped)
- A `jwk` header block (embedded-key injection — no hosting required)
- A `jku` header block (hosted-key injection — needs a URL)
- A JWKS body ready to host at that URL

### Usage
jwtgen
(requires the `jwtgen` alias — see `~/.bashrc`: `alias jwtgen="python3 ~/tools/jwtgen.py"`)

Paste the public JWK when prompted, provide a hosting URL if doing a `jku` attack (or skip for `jwk`-only), and it prints every block needed for both attack variants in one pass.

### Notes

- Never paste a *private* JWK here — only the public half (`kty`, `e`, `kid`, `n`) should ever be pasted or hosted anywhere.
- For algorithm confusion attacks (RS256→HS256), this tool is not what you need — that requires byte-exact PEM handling, which Burp's JWT Editor handles correctly; this script is for `jwk`/`jku` injection only.
