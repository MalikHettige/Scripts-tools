# Bypassing Rate Limits via Race Conditions — Single-Packet Attack

Turbo Intruder script that bypasses a per-username failed-login lockout by racing the check-then-increment counter. Built while solving the PortSwigger lab of the same name.

## Technique

The login endpoint's lockout logic reads the current failure count, checks it against a threshold, and only then writes the incremented count — two separate steps, not one atomic operation. Firing every candidate password as a single-packet burst (all requests held at a gate over one HTTP/2 connection, released together) means every request reads the counter before any of the others' increments commit. The lockout never triggers, and the full password list gets tested in one uninterrupted pass.

## Dependencies

- Burp Suite (Community is fine) with the **Turbo Intruder** extension installed from the BApp Store.
- A candidate password/wordlist on your OS clipboard at runtime (the script reads `wordlists.clipboard`).

## Usage

1. Capture a failed `POST /login` request in Burp, right-click → Extensions → Turbo Intruder → Send to Turbo Intruder.
2. Set `username` to the target account.
3. Highlight the `password` value in the request editor (marks it as the substitution point).
4. Copy your password list to the clipboard.
5. Paste this script into Turbo Intruder's script panel, run the attack.
6. Scan the results table for the response that breaks pattern (e.g. `302 Found` / a redirect to an authenticated page) instead of the expected invalid-credentials or lockout response.

## Generalizing to real targets

- Swap `/login` for any check-then-act limited endpoint: OTP verification, password reset token validation, 2FA attempt limits, coupon/gift-card redemption, withdrawal limits.
- `concurrentConnections=1` + `Engine.BURP2` is the part that matters — it forces everything onto one HTTP/2 connection so the gate release behaves as a true single-packet burst instead of N independently-scheduled connections.
- Only run this against accounts/scope you're authorized to test. Even a small burst (10-20 requests) against someone else's account is still brute-forcing it.

## Related

- Writeup: https://github.com/MalikHettige/Bug-bounty-writeups/blob/main/race-conditions/labs/02-bypassing-rate-limits-via-race-conditions.md
