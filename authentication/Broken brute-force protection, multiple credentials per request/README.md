# Broken Brute-Force Protection: Multiple Credentials Per Request

> Script used to solve the PortSwigger lab: **Broken brute-force protection, multiple credentials per request**  
> Bypasses brute-force lockout by sending all passwords in a single JSON array — the protection counter sees 1 request, the server tries all passwords.

---

## Directory Structure

```
broken-brute-force-multiple-credentials/
├── README.md
├── brute-force-json-array.py    # Single script — enumerate + gain access
```

---

## What to Replace

### File path
```python
with open("C:/Users/malik/Downloads/passwords.txt") as f:
```
Replace with your wordlist path.

### Target URL
```python
base_url = "https://0a06007e0368a5cd8043b7ee0096001b.web-security-academy.net"
```
Replace with your lab or target URL.

### Session cookie
```python
cookies={"session": "YOUR_COOKIE_HERE"}
```
Get a fresh unauthenticated session cookie by loading the login page in incognito and copying the session value from DevTools → Application → Cookies.

### Target username
```python
json={"username": "carlos", "password": passwords}
```
Replace `"carlos"` with your known target username.

---

## Why One Script This Time

Unlike the previous two labs, username enumeration isn't needed here — the username (`carlos`) is already known from the lab brief. This is purely a brute-force bypass, so one script handles everything:

1. Load all passwords from wordlist into a Python list
2. Send them all in a single POST request as a JSON array
3. Server loops through every password internally — protection counter sees 1 attempt
4. A 302 redirect = successful login — grab the new authenticated session cookie
5. Inject cookie into browser and navigate to `/my-account`

---

## Why This Works (The Vulnerability)

The brute-force protection counts **requests**, not **attempts**. When the login endpoint accepts JSON, an attacker can send an array instead of a string:

```json
// Normal — 1 request, 1 attempt
{"username": "carlos", "password": "123456"}

// Exploit — 1 request, 100 attempts
{"username": "carlos", "password": ["123456", "password", "letmein", ...]}
```

The server processes every item in the array — trying each password against the account — but the rate-limit counter only increments once. The protection is completely bypassed.

---

## Why This Is Better Than Burp Suite Community Intruder

| | Burp Community Intruder | This Script |
|---|---|---|
| Speed | ~1 req/sec throttled | 1 request total |
| Lockout risk | High — sends 100 requests | Zero — sends 1 request |
| Detection risk | High request volume | Minimal — looks like 1 login attempt |
| Setup | Manual payload position | Single script run |

This isn't just faster than Burp Community — it's a fundamentally different technique. Even Burp Pro can't do this with standard Intruder since it still sends one request per payload.

---

## How to Get the Session Cookie (Step by Step)

1. Open the lab URL in an **Incognito window**
2. Do NOT log in — just let the page load
3. F12 → **Application** tab → **Cookies** → click the lab domain
4. Copy the `session` value
5. Paste into the script

After the attack, grab the **new session cookie** from the script output and inject it:
1. F12 → Application → Cookies → double-click the session value
2. Replace with the new cookie from script output
3. Navigate to `/my-account?id=carlos`

---

## Real Bug Bounty Application

On a real target, test for this by:
1. Confirming the endpoint accepts `Content-Type: application/json`
2. Sending a JSON body — if it returns the same response as form data, JSON is supported
3. Trying a password array with 2 values first — if no error, scale up to full wordlist
4. Checking if the rate-limit counter resets — some apps lock per IP, some per username

This vulnerability is most common in:
- Custom-built authentication systems
- APIs where developers added brute-force protection to the form but forgot the JSON endpoint
- Mobile app backends

---

## Usage

```bash
python3 brute-force-json-array.py
```

---

## References

- [PortSwigger Lab](https://portswigger.net/web-security/authentication/password-based/lab-broken-brute-force-protection-multiple-credentials-per-request)
- [PortSwigger — Brute-force attacks](https://portswigger.net/web-security/authentication/password-based)
- [OWASP — Testing for Weak Lock Out Mechanism](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/04-Authentication_Testing/03-Testing_for_Weak_Lock_Out_Mechanism)

---

**Tags:** `#PortSwigger` `#Authentication` `#BruteForce` `#JSONInjection` `#RateLimitBypass` `#Expert` `#Python`
