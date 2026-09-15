# Username Enumeration via Different Responses — Scripts

> Scripts used to solve the PortSwigger lab: **Username enumeration via different responses**  
> Faster, concurrent alternative to Burp Suite Community Intruder.

---

## Directory Structure

```
username-enum-different-responses/
├── README.md
├── username-enum-different-responses.py   # Phase 1: find valid username
└── password-brute.py                      # Phase 2: brute-force password
```

---

## What to Replace

### File paths
Both scripts have a wordlist path — replace with your own:
```python
# username-enum-different-responses.py
with open("C:/Users/malik/Downloads/usernames.txt") as f:

# password-brute.py
with open("C:/Users/malik/Downloads/passwords.txt") as f:
```
Point these to wherever you saved the wordlists on your machine.

### Target URL
Both scripts have a `base_url` variable at the top:
```python
base_url = "https://0a20001503bda4858045fdbf00590076.web-security-academy.net"
```
Replace the full URL with your lab instance URL, or your real target's login endpoint.

### Found username (password-brute.py only)
After Phase 1 finds a valid username, paste it into Phase 2:
```python
data={"username": "an", "password": password},
```
Replace `"an"` with whatever your Phase 1 script returned.

---

## Why Two Separate Scripts

The attack is a two-phase process by design:

**Phase 1 — Username enumeration** (`username-enum-different-responses.py`)  
Iterates through a username wordlist with a dummy password. Detects the valid username by checking for a **different error message** — `"Incorrect password"` instead of `"Invalid username"`. Only one username triggers this difference.

**Phase 2 — Password brute-force** (`password-brute.py`)  
Once the valid username is confirmed, iterates through a password wordlist using that username. Looks for an HTTP **302 redirect** — which only happens on a successful login.

Splitting them keeps the logic clean and lets you re-run Phase 2 independently if you need to swap wordlists or adjust threading without re-running enumeration.

---

## Why This Is Better Than Burp Suite Community Intruder

| | Burp Community Intruder | These Scripts |
|---|---|---|
| Speed | Throttled to ~1 req/sec | 10 concurrent threads (configurable) |
| 101 usernames | ~2–3 minutes | ~10 seconds |
| 100 passwords | ~2–3 minutes | ~10 seconds |
| CSRF handling | Manual | Scriptable |
| Automation | GUI only | Fully scriptable, reusable |
| Cost | Free (throttled) | Free, no limit |

Burp Pro removes the throttle — but these scripts are free, faster to run, and easier to adapt per target without clicking through a GUI every time.

---

## Suggestions for Improvement

1. **Add `-t` thread flag as a CLI argument** — so you can tune concurrency from the command line without editing the script (`python3 script.py -t 20`)

2. **Add `--delay` flag** — some targets rate-limit aggressive requests; a configurable per-request delay avoids false negatives

3. **Save output to a file** — pipe results to a `.txt` log automatically so you have proof-of-concept output ready for writeups without screenshotting the terminal

4. **Auto-chain the two phases** — Phase 1 could pass the found username directly into Phase 2 without you having to copy-paste it manually

5. **Add response length logging** — even for `[-]` results, logging the byte size helps you spot anomalies that aren't just text-based (useful when the error difference is size, not wording)

---

## Usage

```bash
# Phase 1 — enumerate username
python3 username-enum-different-responses.py

# Phase 2 — brute-force password (after editing username in script)
python3 password-brute.py
```

---

**Tags:** `#PortSwigger` `#Authentication` `#UsernameEnumeration` `#BruteForce` `#Python`
