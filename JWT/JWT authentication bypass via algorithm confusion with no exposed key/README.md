# JWT Authentication Bypass via Algorithm Confusion (No Exposed Key)

Script used to forge an admin JWT when the server's RS256 public key 
is NOT published anywhere (no `/jwks.json` or similar), requiring the 
public key to be mathematically derived from two valid signed tokens 
instead of fetched directly.

## Dependencies
- `rsa_sign2n` (https://github.com/silentsignal/rsa_sign2n) — derives 
  candidate public keys from two valid RS256-signed JWTs
- Python `hmac`, `hashlib`, `base64`, `json`, `sys` (standard library only)

## Workflow
1. Obtain two valid, differently-signed RS256 tokens from the target 
   (e.g. two separate logins as the same low-privilege user).
2. Run `rsa_sign2n`'s `jwt_forgery.py` against both tokens — it outputs 
   one or more candidate public keys as `.pem` files (derivation from 
   signatures isn't always unique, hence multiple candidates).
3. Before running `forge_token.py`, edit these placeholders in the script:
   - `TARGET_KID_VALUE` — the `kid` from the target's real JWT header
   - `TARGET_ISSUER` — the `iss` from the target's real JWT payload 
     (omit the line if the app doesn't use one)
   - `TARGET_USERNAME` — the identity being forged (e.g. `administrator`)
4. Run the script, passing each candidate PEM filename as an argument, 
   until one produces a working forged token:

```bash
python forge_token.py candidate1.pem
python forge_token.py candidate2.pem
```
5. Test each output token against the protected endpoint.

---
### full install block
**For linux users**

```bash
# Linux VM version of the pip installs above
pip install gmpy2 --break-system-packages
pip install asn1tools --break-system-packages
pip install pycryptodomex --break-system-packages
pip install ratelimit --break-system-packages
pip install termcolor --break-system-packages
```
**For users with windows or anything other than Linux, use Git bash**

```bash
# Core dependencies for rsa_sign2n (public key derivation)
pip install gmpy2
pip install asn1tools
pip install pycryptodomex

# jwt_tool dependencies (only needed if also using jwt_tool directly, 
# not required for forge_token.py alone)
pip install ratelimit
pip install termcolor

# Clone the tools (skip if already cloned)
git clone https://github.com/ticarpi/jwt_tool
git clone https://github.com/silentsignal/rsa_sign2n
```

## Related writeup
https://github.com/MalikHettige/Bug-bounty-writeups/blob/main/[path-to-writeup].md
