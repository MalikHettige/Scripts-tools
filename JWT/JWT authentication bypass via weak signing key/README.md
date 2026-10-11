# JWT Weak Signing Key — Unified Solver

A single script that replaces the old two-step `cracking_script.py` + `forge_the_admin_token.py` workflow. It takes your captured JWT and a wordlist, brute-forces the HS256 signing secret, and forges a new token with a chosen `sub` claim — all in one run, with no manual editing of the script itself (everything is passed as command-line arguments).

## What this is for

The lab's session cookie is a JWT signed with `HS256` (a symmetric algorithm — the same secret both signs and verifies). The secret is weak enough to be guessed from a common wordlist. Once cracked, you can mint your own validly-signed token claiming to be any user, including `administrator`.

**Trigger condition:** any time a JWT header shows `"alg": "HS256"`, this is worth trying by default — weak/shared HMAC secrets are common.

**Horizontal access note:** this script also works for horizontal privilege escalation — pass `--sub <victim-username>` instead of `administrator` to take over a specific account.

## Requirements

- Python 3
- The `PyJWT` package (**not** the unrelated `jwt` package — see Troubleshooting below)

## Just want one result? (no repo, no setup)

```bash
curl -o jwt_weak_key_solver.py "https://raw.githubusercontent.com/MalikHettige/scripts-tools/main/JWT/JWT%20authentication%20bypass%20via%20weak%20signing%20key/unified-solver/jwt_weak_key_solver.py"
curl -o jwt.secrets.list "https://raw.githubusercontent.com/wallarm/jwt-secrets/master/jwt.secrets.list"
python3 -m pip install PyJWT --break-system-packages
python3 jwt_weak_key_solver.py --token "<your captured JWT>" --wordlist jwt.secrets.list --sub administrator
```

Delete `jwt_weak_key_solver.py` and `jwt.secrets.list` afterward if you don't need them again.

## Frequent use (clone and keep)

```bash
git clone https://github.com/MalikHettige/scripts-tools.git "$HOME/Documents/GitHub/Scripts-tools"
```

Then, from anywhere:

```bash
python3 -m pip install PyJWT --break-system-packages
python3 "$HOME/Documents/GitHub/Scripts-tools/JWT/JWT authentication bypass via weak signing key/unified-solver/jwt_weak_key_solver.py" \
  --token "<your captured JWT>" \
  --wordlist "$HOME/Documents/GitHub/Scripts-tools/JWT/JWT authentication bypass via weak signing key/unified-solver/jwt.secrets.list" \
  --sub administrator
```

(The wordlist isn't checked into the repo — download it once with the `curl` command above and keep it alongside the script.)

## Ordered steps

1. Capture your session JWT (Burp Proxy → HTTP history, or your browser's cookie storage).
2. Confirm `alg` is `HS256` by decoding the token (jwt.io, or Burp's JSON Web Token tab).
3. Download the wordlist linked from the lab page itself — for the PortSwigger lab this is [`wallarm/jwt-secrets/jwt.secrets.list`](https://github.com/wallarm/jwt-secrets/blob/master/jwt.secrets.list). Using a generic list (e.g. rockyou.txt) usually won't contain the lab's planted secret.
4. Install `PyJWT` (see Requirements/Troubleshooting).
5. Run the script:
   ```bash
   python3 jwt_weak_key_solver.py --token "<your JWT>" --wordlist jwt.secrets.list --sub administrator
   ```
6. It prints the cracked secret and a forged token. Replace your session cookie with that forged value.
7. Browse to `/admin`, then delete the target user (e.g. `/admin/delete?username=carlos`) to solve the lab.

## Troubleshooting / gotchas actually hit while testing this

- **`ModuleNotFoundError: No module named 'jwt.api_jwk'`** — this happens if the unrelated PyPI package named `jwt` ever got installed alongside `PyJWT`. Both packages install under the same top-level `import jwt`, and one silently overwrites files from the other, leaving a broken, incomplete module. Fix:
  ```bash
  python3 -m pip uninstall jwt PyJWT -y
  python3 -m pip install PyJWT --break-system-packages
  python3 -c "import jwt; print(jwt.__version__)"
  ```
  The last line should print a clean version number with no traceback before you run the solver.
- **`python3`/`pip3` pointing to different installs** — if `pip3 install` succeeds but the script still reports the dependency missing, run `which python3` and `which pip3` to check they resolve to the same install. If not, install directly through the interpreter the script actually runs with: `python3 -m pip install PyJWT --break-system-packages`.
- **"No such file or directory" running the script** — you're not in the folder the script is saved in. `cd` into that folder first, or pass the script's full path.
- **No match found in the wordlist** — confirm you downloaded the *exact* wordlist linked on the lab page, not a generic one; the planted secret is deliberately only in that list.
- **`pip`/dependency-resolver conflict warnings** (e.g. a warning that some other tool like `semgrep` wants a different `PyJWT` version) — these are informational only and don't block the install; the script will still work with the version actually installed.

## Legacy two-script version

The original two-step approach (`cracking_script.py` then `forge_the_admin_token.py`, edited by hand per-run) still lives one directory up, in `JWT/JWT authentication bypass via weak signing key/`. This unified script supersedes it for day-to-day use — same underlying method, no manual script editing required.
