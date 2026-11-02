# Authentication Bypass via Encryption Oracle

Helper for labs/targets where an app encrypts user-controlled input and reflects the ciphertext (e.g. a `notification`/error cookie), **and** separately decrypts a user-supplied cookie and reflects the plaintext (e.g. in an error message) — using the same key for both. That combination lets you forge arbitrary plaintext (like `administrator:<timestamp>`) and get it encrypted under the app's own key, with no knowledge of the key itself.

This script automates the block-cipher math: given the server's error text and your known submitted plaintext, it tells you the fixed prefix length the server injects, how many bytes you need to strip to remove it cleanly (rounded to the cipher's block size — AES = 16 bytes), and how much junk padding to prepend on your next encrypt request so the strip lands on a clean block boundary.

**Trigger condition:** two+ cookies from the same app that look like opaque high-entropy binary (no `eyJ` JWT prefix, length always a multiple of 16), where at least one reflects decrypted attacker-supplied ciphertext somewhere (an error message, a confirmation page) and at least one reflects encrypted attacker-supplied plaintext somewhere.

## Requirements

- Python 3
- No external packages — standard library only (`base64`, `urllib.parse`, `argparse`)

## Just want one result? (no repo, no setup)

```bash
curl -o oracle_stripper.py "https://raw.githubusercontent.com/MalikHettige/scripts-tools/main/business-logic/Authentication%20bypass%20via%20encryption%20oracle/oracle_stripper.py"
python3 oracle_stripper.py --cookie "<url-encoded notification cookie>" --error-message "<exact error text>" --known-plaintext "<exact string you submitted>"
```

Delete `oracle_stripper.py` afterward if you don't need it again.

## Frequent use (clone and keep)

```bash
git clone https://github.com/MalikHettige/scripts-tools.git "$HOME/Documents/GitHub/Scripts-tools"
```

Then, from anywhere:

```bash
python3 "$HOME/Documents/GitHub/Scripts-tools/business-logic/Authentication bypass via encryption oracle/oracle_stripper.py" \
  --cookie "<url-encoded notification cookie>" \
  --error-message "<exact error text>" \
  --known-plaintext "<exact string you submitted>"
```

## Ordered steps (two-pass workflow)

This is a **two-pass** process — the first run only tells you the padding you need, it doesn't give you a usable cookie yet.

1. **Find the oracle pair.** Submit invalid input to the encrypt feature (e.g. an email field), confirm it sets a new opaque cookie. Submit your real auth cookie (e.g. `stay-logged-in`) into the decrypt feature's cookie slot, confirm it gets reflected in cleartext in an error message. If it decrypts to something readable, you've confirmed shared key + learned the plaintext format (e.g. `username:timestamp`).

2. **First pass — measure the prefix.** Submit your target plaintext (e.g. `administrator:<timestamp>`) through the encrypt feature with no padding. Grab the resulting cookie and the resulting error message from decrypting it. Run:
   ```bash
   python3 oracle_stripper.py \
     --cookie "<cookie from step 2>" \
     --error-message "<exact error text from decrypting it>" \
     --known-plaintext "administrator:<timestamp>"
   ```
   This won't produce a usable stripped cookie — it'll tell you how much junk padding to add next.

3. **Second pass — apply the padding.** Re-submit through the encrypt feature with that many junk characters (`x`) prepended to your target plaintext. Grab the NEW cookie and NEW error message. Run the script again with the padded `--known-plaintext` and the new `--cookie`/`--error-message`. This time it prints a usable stripped cookie.

4. **Verify before using it.** Paste the stripped cookie into the decrypt feature's cookie slot and confirm the response shows your target plaintext exactly, with no prefix and no junk characters left over.

5. **Deploy.** Drop the verified stripped cookie into the real authentication cookie slot (e.g. `stay-logged-in`), remove any session cookie that would take priority, and send.

**It would look like:**
```
Detected prefix length:        23
Total ciphertext bytes:        64
Bytes to strip (block-aligned): 32
Junk padding needed on next encrypt: 9
Prepend to your plaintext next time:  xxxxxxxxxadministrator:1793601652468

Stripped + re-encoded cookie (paste into the decrypt request):
gZ2gc2v3oIbmnPGLwSeurdvKcgLXmpv9WKG7qnGzS30%3D
```

## Troubleshooting / gotchas actually hit while testing this

- **"Couldn't find your plaintext in the error message"** — your `--known-plaintext` has to match the error text **exactly**, including any junk padding you already added. Copy-paste it directly from the actual request you sent, don't retype it.
- **Script runs but no stripped cookie is printed** — this is expected on the first pass (unpadded). It only confirms the math; you still need to re-encrypt with the reported padding and run the script again on that new output.
- **Stripping the wrong byte count** — don't apply a strip count computed from an *unpadded* ciphertext to a *different* ciphertext. The strip math is only valid for the exact ciphertext it was computed against.
- **Pasted the script into a shell instead of running it as Python** — if you see `bash: import: command not found` or a wall of `syntax error near unexpected token`, you pasted Python into a bash prompt. Save it to a `.py` file and run with `python3 oracle_stripper.py ...`, or use the one-liner from a proper Python context.

## Related writeup

https://github.com/MalikHettige/Bug-bounty-writeups/blob/malikhettige-lab-report-loop/business-logic/labs/lab%20-%20Authentication%20Bypass%20via%20Encryption%20Oracle.md
