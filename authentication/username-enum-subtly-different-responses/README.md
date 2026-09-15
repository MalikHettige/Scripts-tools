# Username Enumeration via Subtly Different Responses — Scripts

> Scripts used to solve the PortSwigger lab: **Username enumeration via subtly different responses**  
> Harder than the previous lab — the error message looks identical to the naked eye.

---

## Directory Structure

```
username-enum-subtly-different-responses/
├── README.md
├── username-enum-subtly-different-responses.py   # Phase 1: find valid username
└── password-brute.py                              # Phase 2: brute-force password
```

---

## What Makes This Different From the Previous Lab

In the previous lab (`username-enum-different-responses`), the app returned two visually distinct messages:
- `"Invalid username"` → user doesn't exist
- `"Incorrect password"` → user exists

Here, **both cases return the exact same message:**
> `"Invalid username or password."`

The difference is a **single invisible trailing space** — `"Invalid username or password. "` for valid usernames vs `"Invalid username or password."` for invalid ones. You cannot see it in a browser. You cannot see it in Burp's rendered view. Python can.

---

## What to Replace

### File paths
```python
# username-enum-subtly-different-responses.py
with open("C:/Users/malik/Downloads/usernames.txt") as f:

# password-brute.py
with open("C:/Users/malik/Downloads/passwords.txt") as f:
```
Replace with the path to your wordlists.

### Target URL
```python
base_url = "https://0a5500f90411675380a99941001c0077.web-security-academy.net"
```
Replace with your lab instance URL or real target login endpoint.

### Found username (password-brute.py only)
```python
data={"username": "ag", "password": password}
```
Replace `"ag"` with whatever Phase 1 returns.

---

## Why Two Separate Scripts

**Phase 1 — Username enumeration** (`username-enum-subtly-different-responses.py`)  
Sends POST requests with each candidate username and a dummy password. Detects the valid username by checking whether the exact string `"Invalid username or password."` is **absent** from the response — meaning the server returned a subtly different variant (trailing space) that doesn't match the hardcoded string.

**Phase 2 — Password brute-force** (`password-brute.py`)  
Uses the confirmed valid username and iterates through a password wordlist. A correct password triggers an HTTP **302 redirect** — the only reliable signal of a successful login.

Same two-phase logic as the previous lab, different detection method in Phase 1.

---

## Why This Is Harder Than the Previous Lab

| | Different Responses | Subtly Different Responses |
|---|---|---|
| Error message | Visually distinct | Looks identical |
| Detectable by eye | ✅ Yes | ❌ No |
| Detectable in browser | ✅ Yes | ❌ No |
| Detectable by Burp UI | ✅ Yes | ❌ Nearly impossible |
| Detection method | String match | Absent string / trailing space |
| Noise from dynamic content | Low | High (analytics IDs, session cookies change every request) |

The dynamic content (analytics IDs, session tokens) made byte-count and body-diff approaches unreliable — every response looked different even for the same username. The correct solution was to anchor on the **exact absence of a known fixed string** rather than comparing full response bodies.

---

## Why This Is Better Than Burp Suite Community Intruder

| | Burp Community Intruder | These Scripts |
|---|---|---|
| Speed | ~1 req/sec throttled | 10 concurrent threads |
| Subtle difference detection | Manual column comparison | Automated string absence check |
| Dynamic content noise | Pollutes length column | Handled by string anchoring |
| Reusability | GUI, per-session setup | Script, reusable instantly |
| Cost | Free (throttled) | Free, no limit |

---

## Lessons Learned

- When byte count and body diff both fail due to dynamic content, **anchor on a known fixed string** instead
- A trailing space is enough to enumerate users — the vulnerability doesn't need to be obvious
- `"Identical" responses are rarely truly identical` — always check at the byte/char level before concluding there's no difference
- This pattern shows up in real applications where developers copy-paste error messages and accidentally introduce whitespace inconsistencies

---

## Usage

```bash
# Phase 1 — enumerate username
python3 username-enum-subtly-different-responses.py

# Phase 2 — brute-force password (edit username in script first)
python3 password-brute.py
```

---

## References

- [PortSwigger Lab](https://portswigger.net/web-security/authentication/password-based/lab-username-enumeration-via-subtly-different-responses)
- [OWASP — Testing for Account Enumeration](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/03-Identity_Management_Testing/04-Testing_for_Account_Enumeration_and_Guessable_User_Account)

---

**Tags:** `#PortSwigger` `#Authentication` `#UsernameEnumeration` `#BruteForce` `#Practitioner` `#Python`
