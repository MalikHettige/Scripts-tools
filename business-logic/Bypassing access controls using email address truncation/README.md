# Truncation-Based Domain Check Bypass

Builds a padded email address that exploits a mismatch between a server's **stored (truncated)** field length and the domain actually used for **mail delivery**. If a registration email field gets silently truncated to N characters before being stored/checked, but the mail server sends to whatever full, untruncated address you actually submitted, you can register with an address that *looks* like it ends in a trusted domain once truncated, while mail still delivers to a domain you control.

**Trigger condition:** a domain-restricted signup flow (same family of bugs as the email-parsing-discrepancy script in this repo) where you suspect the registration field has a length limit that isn't enforced consistently between storage and delivery.

## Requirements

- Python 3, standard library only

## Critical: confirm the real cutoff first

**255 is NOT a universal truncation limit.** It's one specific backend's behavior (common because it's `2^8 - 1`, the classic legacy `VARCHAR(255)` convention). Real targets may truncate at a different length, not at all, or at different lengths in different fields (registration vs access-check vs display).

**Before trusting any cutoff number:**
1. Register with a huge dummy string (1000+ characters, no exploit payload — just padding).
2. Authenticate and check where it got cut: My Account page, a password-reset email, or any other point that echoes the stored value back to you.
3. Count the stored string's exact length — `echo -n "PASTED_STORED_VALUE" | wc -c`.
4. Pass that confirmed number as `--cutoff`.

If no field anywhere echoes the stored value back, you have no way to confirm the cutoff — don't guess blind with this technique; fall back to common conventions (255, 254 per RFC 5321, 100, 50) only as a last resort, testing each.

## Usage

```bash
python3 truncation_email.py \
  --trusted-domain <the domain the app's validator checks for> \
  --real-domain <your actual mail-receiving domain> \
  --cutoff <confirmed truncation length — see above>
```

Example:

```bash
python3 truncation_email.py \
  --trusted-domain dontwannacry.com \
  --real-domain exploit-0a3200230339e43c8152158901db005c.exploit-server.net \
  --cutoff 255
```

Output:

```
aaaa...aaa@dontwannacry.com.exploit-0a3200230339e43c8152158901db005c.exploit-server.net
Padding length: 238
Position of trusted domain's last char: 255
Total email length: 315
```

Paste the full printed email as the registration email field's value. The server truncates it to `--cutoff` characters for storage (landing exactly at the end of `@<trusted-domain>`), while the mail client still delivers to the real, full domain — letting you receive and click the confirmation link.

## Ordered steps

1. Confirm the domain restriction exists (try a normal non-matching email, note the rejection message).
2. Register with a huge dummy string to find and confirm the real truncation cutoff (see "Critical" section above) — do not assume 255.
3. Run this script with the confirmed `--cutoff`.
4. Paste the output email into the registration form.
5. Check your real inbox (exploit server / webhook) for the confirmation email and complete registration.
6. Confirm the account received the expected elevated access.

## Troubleshooting

- **Padding math looks off / technique doesn't land where expected** — double check you're using the *confirmed* cutoff, not an assumed one. A wrong cutoff silently shifts where the trusted domain's last character lands relative to the truncation point.
- **Confirmation email never arrives** — verify `--real-domain` is exactly correct (typos here misroute the email entirely, unrelated to the truncation logic).
- **Script raises a "won't fit" error** — the trusted domain + your real domain combined are already longer than the cutoff allows; this specific technique isn't viable at that cutoff length.
