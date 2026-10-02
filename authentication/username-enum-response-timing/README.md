# Pre-Engagement Checklist — Before Running Any Script on a Real Target

Run through this every time, before executing a script against a live bug bounty program. This exists because scripts fail silently, scope violations are not forgivable, and "I didn't prepare" is not a defense to a program.

## 1. Scope & Authorization

- [ ] Program's scope page open and re-read — not from memory
- [ ] Target domain/subdomain is explicitly in scope (not just "looks related")
- [ ] Check for out-of-scope exclusions (specific endpoints, third-party integrations, rate-limit-sensitive areas)
- [ ] Confirm the vuln class you're testing is allowed (some programs exclude brute-force/DoS-adjacent testing, rate-limit testing, or require prior written permission for anything resembling automated attacks)
- [ ] If anything is ambiguous — stop and ask the program, don't assume

## 2. Script Readiness

- [ ] Script saved to a real file (`.py`), not pasted directly into terminal
- [ ] Confirmed with `cat filename.py` that what's saved matches what you intend to run — don't trust memory of what you pasted
- [ ] `base_url` (and any other target-specific variable) updated to the REAL target — not leftover lab/placeholder values
- [ ] Removed any trailing slash mismatches in URLs (`example.com/` + `/login` = broken double-slash)
- [ ] Dry-run against a throwaway/safe value first if the script has destructive potential (e.g. test `--dry-run` mode before live mode)

## 3. Rate Limiting & Safety

- [ ] Know the program's stated rate limits (check scope page / program rules) — do not exceed them
- [ ] Add delays between requests if hammering an endpoint (`time.sleep()`), especially for anything resembling brute-force
- [ ] Know what "locked out" looks like for this target BEFORE you trigger it (status code, response body, redirect) — so you recognize it immediately instead of burning more attempts
- [ ] If testing anything auth-related, have a plan for IF you get locked out (wait time? reset mechanism? do you even have more attempts budgeted?)
- [ ] Never run a brute-force/enum script against a real target the same way you did on a lab — real targets usually need FEWER requests, more precision, not raw wordlist grinding

## 4. Baseline Before Automating

- [ ] Manually test the request ONCE in Burp Repeater first — confirm you understand the exact request/response shape before scripting it
- [ ] Confirm you know what a "success" response looks like (status code, body content, timing) before writing conditional logic for it
- [ ] Confirm what a normal/expected "failure" response looks like, so your script doesn't misinterpret noise as a finding

## 5. Evidence Collection Plan

- [ ] Know BEFORE running what you'll need to screenshot/log if it works (raw request + response pairs, not just a script printout)
- [ ] Script prints enough detail to reconstruct the finding later (timestamps, exact payloads used, status codes) — not just "success/fail"
- [ ] If using timing analysis: plan to run enough repeats (5-7 minimum) to average out noise BEFORE drawing conclusions — one data point proves nothing

## 6. Root Cause Clarity

- [ ] Before writing any code, can you state in one sentence WHY this should work (the root cause), not just WHAT you're about to run?
- [ ] If you can't explain the root cause without the script, you're not ready to automate it — go back and manually confirm the mechanism first (Repeater, manual requests)

## 7. Post-Run Sanity Check

- [ ] Do the results make sense given what you expected? (e.g. if testing timing and both numbers are identical and suspiciously slow — that's probably an error page, not your signal)
- [ ] Re-run before trusting a single data point — noise is the default assumption until proven otherwise
- [ ] Only write up / report once the finding is consistent across repeats, not a one-off

## Quick Reminder

Scripts are a precision tool, not a shortcut around understanding. If you can't explain to yourself (or me) exactly what the script is testing and why, in one sentence, before you run it — stop and go back to manual testing in Burp first.


# For solving the lab easily

> Scripts used to solve the PortSwigger lab: **Username enumeration via response timing**  
> Detects valid usernames by measuring bcrypt execution time difference. Bypasses IP rate limiting via X-Forwarded-For spoofing.

## Directory Structure

```
username-enum-response-timing/
├── README.md
├── username-enum-timing.py    # Phase 1: timing attack to find valid username
└── password-brute.py          # Phase 2: brute-force with IP rotation
```

## What to Replace

### File paths
```python
with open("C:/Users/malik/Downloads/usernames.txt") as f:
with open("C:/Users/malik/Downloads/passwords.txt") as f:
```

### Target URL
```python
base_url = "https://YOUR-LAB-ID.web-security-academy.net"
```

### Found username (password-brute.py)
```python
data={"username": "alterwind", "password": password}
```
Replace `"alterwind"` with whatever Phase 1 returns.

## Why This Is Harder Than Previous Labs

| Lab | Signal | Detectable by |
|---|---|---|
| Different responses | Error message text | Eyes / Burp |
| Subtly different | Trailing space | Python string check |
| Response timing | Milliseconds | Python timer only |

No visual difference. No byte difference. Pure time measurement.

## Why Two Scripts

**Phase 1** runs 3 timed requests per username and averages them — reduces network jitter. Sorts all results by slowest. The outlier is the valid username.

**Phase 2** brute-forces the confirmed username with a rotating `X-Forwarded-For` IP per request to bypass the rate limiter.

## The X-Forwarded-For Bypass

The app rate-limits by IP using the `X-Forwarded-For` header — which is spoofable:

```python
fake_ip = f"192.168.{i // 256}.{i % 256}"
headers = {"X-Forwarded-For": fake_ip}
```

Each request appears to come from a different IP. Rate limiter never triggers.

**Also try on real targets:** `X-Real-IP`, `X-Client-IP`, `True-Client-IP`

## Usage

```bash
# Phase 1 — find valid username via timing
python3 username-enum-timing.py

# Phase 2 — brute-force password (edit username first)
python3 password-brute.py
```
**Tags:** `#TimingAttack` `#XForwardedFor` `#RateLimitBypass` `#Python` `#PortSwigger`
