# JWK Header Builder

A small local utility for preparing JWT headers and a hosted JWKS from an RSA JWK. It keeps only public key fields in generated output, so private key parameters are not copied into the JWT header or JWKS.

## Requirements

- Python 3
- No external packages; the script uses only the Python standard library.

## Just want one result? (no repo, no setup)

If you only need this once and don't want to clone the repo, download the single script and run it:

```bash
curl -o jwt_header_builder.py "https://raw.githubusercontent.com/MalikHettige/scripts-tools/main/JWT/JWT%20authentication%20bypass%20via%20jwk%20header%20injection/jwt_header_builder.py"
python3 jwt_header_builder.py
```

Then follow the prompts below. Delete the script afterward if you don't need it again.

## Frequent use (clone and keep)

If you hunt with this regularly, clone the repo once and run it by path whenever you need it:

```bash
git clone https://github.com/MalikHettige/scripts-tools.git "$HOME/Documents/GitHub/Scripts-tools"
```

Then, from anywhere:

```bash
python3 "$HOME/Documents/GitHub/Scripts-tools/JWT/JWT authentication bypass via jwk header injection/jwt_header_builder.py"
```

To stay current, `cd` into the cloned folder and `git pull` before a session.

## What happens when you run it

Paste either a raw RSA JWK or a JWKS JSON object when prompted. Multiline JSON is supported. If a JWKS contains multiple RSA keys, the script uses the first one. After the key JSON is accepted, paste the URL where you plan to host the JWKS.

The script then prints:

1. The clean public RSA JWK.
2. A JWT header with the public JWK embedded in its `jwk` field.
3. A JWT header with the supplied URL in its `jku` field.
4. Exploit-server-ready output at the bottom: file path `/exploit`, `Content-Type: application/json`, and the full JWKS body to host at that URL.

**This is how it'd show**
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/100dbce6-2b41-4078-bb44-0bd151aad7da" />

If the input key includes a `kid`, it is retained in the public JWK and generated headers. If it has no `kid`, the outer header uses `<SET_KID>` as a reminder to set a matching key ID before using the output.

## Use a JSON file instead

The script also accepts a file path containing a raw RSA JWK or JWKS:

```bash
python3 jwt_header_builder.py key.json
```

It will prompt for the hosted JWKS URL after loading the file. For example, to create a file from a pasted JSON block:

```bash
cat > key.json <<'EOF'
<paste your RSA JWK or JWKS JSON here>
EOF
python3 jwt_header_builder.py key.json
```

Delete the input file when you no longer need it, especially if it contains private RSA parameters.

## Using the output

- Copy the `jwk` header into the JWT header when testing a `jwk` header configuration.
- Use the `jku` header and host the printed JWKS body at the matching exploit-server path when testing a `jku` header configuration.
- The script only transforms JSON locally. It does not sign tokens, host the JWKS, or send network requests. Configure the exploit server response with the printed path, content type, and body.

When signing a test token, use the same RSA key whose public half is embedded in the `jwk` header or served in the JWKS. Keep the key ID (`kid`) consistent with the key used by the target test setup.
