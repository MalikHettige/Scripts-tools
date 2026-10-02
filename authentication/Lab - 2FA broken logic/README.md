## Purpose

## For real world hunt
- Go the the python file
- Press and hold Ctrl + F to find, search up `vicitm` and `cookie`, `URL` and replace with the real data.
- Execute in Linux terminal or Git bash

### The results would look like this
<img width="1269" height="252" alt="image" src="https://github.com/user-attachments/assets/7380412c-62cc-42e6-afc9-014eb039996d" />

# REAL-WORLD WARNING — BEFORE POINTING THIS AT A LIVE PROGRAM:
- This script was built for a PortSwigger lab, which expects high-volume abuse.
- A real target's WAF/fraud detection WILL likely flag 10,000 rapid requests as an attack.
- Before running this against any real program:
  -Check the program's scope page for automated-testing / rate-limit rules — follow them exactly.
- If unclear, message the program first and ask permission for automated 2FA testing.
- Don't run the full 10,000-code sweep live. Instead:
       - Run ONE request with verify=<your_second_account> to prove the binding is broken.
       - Manually send 5-10 wrong codes (no script) to check for rate-limiting.
- If you must prove full exploitability, drop max_workers to 2-3 and add time.sleep(0.1-0.3)
- between requests, and stop early (e.g. after 500 attempts) once the "no throttling" pattern is clear —
- you don't need to exhaust all 10,000 to make the point.
- Partial proof + extrapolated math in your report beats a full live brute-force almost every time.

**Lab:** PortSwigger Web Security Academy — 2FA broken logic

This script was written specifically for the lab to demonstrate the **broken 2FA verification logic**.

### What it does

* Uses my authenticated lab session.
* Sets `verify=carlos` to target Carlos during the lab's verification step.
* Requests Carlos's 2FA page to trigger/generate a code.
* Concurrently tries all **4-digit MFA codes (`0000–9999`)**.
* Stops when the application returns `302`, indicating a successful 2FA verification.

### Why I wrote it

The lab's 2FA implementation allows the verification step to be attacked independently of the normal login flow. The script automates the repetitive 4-digit code attempts instead of testing them manually.

**Important:** This is a **lab-specific proof-of-concept**, not a general-purpose attack tool. The `LAB_URL` and session cookie are placeholders and must only be used with an authorized lab environment.

### Key pattern learned

> **When MFA verification has a small predictable code space, check whether rate limiting, attempt limits, or proper session/user binding prevent systematic guessing.**
