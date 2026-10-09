# JWT Authentication Bypass via Algorithm Confusion (No Exposed Key)

Scripts used to forge an admin JWT when the server's RS256 public key 
is NOT published anywhere (no `/jwks.json` or similar), requiring the 
public key to be mathematically derived from two valid signed tokens 
instead of fetched directly.

## Dependencies
- `rsa_sign2n` (https://github.com/silentsignal/rsa_sign2n) — derives 
  candidate public keys from two valid RS256-signed JWTs
- Python `hmac`, `hashlib`, `base64`, `json` (standard library only for 
  the forging scripts themselves)

## Workflow
1. Obtain two valid, differently-signed RS256 tokens from the target 
   (e.g. two separate logins as the same low-privilege user).
2. Run `rsa_sign2n`'s `jwt_forgery.py` against both tokens — it outputs 
   one or more candidate public keys as `.pem` files (derivation from 
   signatures isn't always unique, hence multiple candidates).
3. For each candidate `.pem`, run the matching forge script here — it 
   reads the raw PEM bytes and uses them directly as the HS256 HMAC 
   secret (the "confusion" — RS256's public key reused as HS256's key) 
   to sign a forged token with `sub: administrator`.
4. Test each forged token against the protected endpoint until one 
   succeeds (candidate #1 failed in testing, candidate #2 worked — 
   keep trying all candidates if the first doesn't land).

## Usage
```bash
python forge_admin_candidate1.py
python forge_admin_candidate2.py
```
Each prints a complete forged JWT. Edit the `kid` and payload fields 
in the script to match your target's token structure before running.

## Related writeup
https://github.com/MalikHettige/Bug-bounty-writeups/blob/main/[path-to-writeup].md
