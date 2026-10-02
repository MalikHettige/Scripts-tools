# Response-timing-demonstration.py

Tests whether a login endpoint leaks valid usernames via response timing — compares average response time for a known-fake username vs a known/candidate username over multiple repeats, to confirm a timing oracle.

## Before executing everything, make sure to update the script to your context
1. In the script there is `base_url =`, replace its value with the target site's URL. Don't append with a slash.
2. In `for username in` parameter:
- Replace `"REPLACE_WITH_KNOWN_FAKE_USERNAME"` with a username certainly-doesn't-exist control.
- Replace `REPLACE_WITH_YOUR_OWN_TEST_ACCOUNT` with your test account you use to attack
- I Added a third slot `REPLACE_WITH_CANDIDATE_USERNAME` — since in real hunting I need all three. This 3rd one has to be something you aren't certain to exist, it's just random like `firstname.lastname@targetdomain.com`. Use this format if you want.

> The real candidate username should derived from a REAL employee name you found via LinkedIn/OSINT. you don't know if this exact person/format is correct, that's what you're testing

4. X-Forwarded-For header — flagged as optional since not every target's rate-limiting setup needs this; blindly spoofing headers at a real target without knowing if it's needed is unnecessary noise.

## 1. Time to create the script

If the file doesn't already exist in this directory:

```bash
nano response-timing-demonstration.py
```

Paste the script contents in, then save and exit: 
[Click this file to execute the script I built](https://github.com/MalikHettige/Scripts-tools/blob/main/authentication/username-enum-response-timing/response-timing-demonstration.py)

```
Ctrl+O   (write out / save)
Enter    (confirm filename)
Ctrl+X   (exit nano)
```

Confirm it saved correctly before running anything:

```bash
cat response-timing-demonstration.py
```

Check the output matches what you intended to paste — don't trust memory.

## 2. Edit before running

Every time you point this at a new target, update:

- `base_url` — the target's root URL, **no trailing slash**
- `usernames` list — swap `fakeuser123` / `wiener` for your known-fake baseline and the real/candidate username you're testing
- `attempts` — default is 7; raise it if results look noisy

## 3. Run it

```bash
python3 response-timing-demonstration.py
```

## 4. What the output looks like

<img width="593" height="351" alt="image" src="https://github.com/user-attachments/assets/7d158b13-4611-44db-91d6-f19b79a99856" />

## 5. How to read it

- Both usernames should return the same status code (usually `200`) — the oracle is in the **timing**, not the status.
- Compare the two **average** lines, not single attempts — one-off numbers are noise.
- A consistent gap (tens to hundreds of ms) held across most attempts = real oracle. One outlier attempt is fine; ignore it.
- If the averages are close and the two usernames' individual attempts overlap heavily — inconclusive, re-run with more attempts or investigate another angle (response length/content instead).

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
