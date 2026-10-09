# Scripts-tools

## Highlights
- [Broken brute-force protection — multiple credentials per request](https://github.com/MalikHettige/Scripts-tools/blob/main/authentication/Broken%20brute-force%20protection%2C%20multiple%20credentials%20per%20request/README.md)
- [JWT algorithm confusion — no exposed key](https://github.com/MalikHettige/Scripts-tools/blob/main/JWT/JWT%20authentication%20bypass%20via%20algorithm%20confusion%20with%20no%20exposed%20key/README.md)
  
Scripts and tooling for bug bounty hunting — organized by vulnerability class, built while solving PortSwigger labs and adapted for real-world (RW) use. Each subfolder targets a specific technique, with a README explaining the mechanism, dependencies, and generic usage. 

## Structure

Scripts are organized by vulnerability category, e.g.:

- `JWT/` — JWT forgery and bypass techniques (weak secret cracking, alg:none, kid path traversal, jwk header injection, algorithm confusion with and without exposed keys)
- `authorization/` — access control testing tools, including the IDOR matrix tester in `authorization/idor-matrix/`


## Philosophy

Most scripts here started as one-off solutions to a specific lab, then got generalized with placeholder values (uppercase, e.g. `TARGET_USERNAME`) so they're directly reusable against real targets without rewriting from scratch. Each subfolder's own README documents the specific technique, required dependencies, and exact usage.

## Related

- Writeups: https://github.com/MalikHettige/Bug-bounty-writeups
