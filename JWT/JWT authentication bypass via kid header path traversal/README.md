# JWT Authentication Bypass via kid Header Path Traversal

Script used to forge a validly-signed JWT when the server's `kid` header 
value can be manipulated via path traversal to point at `/dev/null` 
(a guaranteed-empty file on Linux), making the effective HS256 signing 
key an empty byte string.

PyJWT rejects empty HMAC keys by design (`InvalidKeyError: HMAC key 
must not be empty`), so this script bypasses the high-level library 
entirely and constructs the signature manually using Python's `hmac` 
and `hashlib` modules.

## Usage
```bash
python forge_empty_key.py
```
Outputs a complete forged JWT (header.payload.signature) with 
`kid` set to a traversal path and `sub` set to `administrator`. 
Adjust the `../` depth in the `kid` value and the payload fields 
to match your target.

## Related writeup
https://github.com/MalikHettige/Bug-bounty-writeups/blob/main/[path-to-this-writeup].md
