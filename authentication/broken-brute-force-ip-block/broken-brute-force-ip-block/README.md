# Broken Brute-Force Protection: IP Block

> Script used to solve PortSwigger lab: **Broken brute-force protection, IP block**  
> Bypasses IP-based lockout by interleaving a valid login between each brute-force attempt — resetting the counter every time.

---

## Directory Structure

```
broken-brute-force-ip-block/
├── README.md
└── ip-block-bypass.py
```

---

## What to Replace

### File path
```python
with open("C:/Users/malik/Downloads/passwords.txt") as f:
```

### Target URL
```python
base_url = "https://YOUR-LAB-URL.web-security-academy.net"
```

### Valid credentials (your test account)
```python
data={"username": "wiener", "password": "peter"}
```
Replace with your own account credentials on the real target.

### Target username
```python
data={"username": "carlos", "password": password}
```
Replace `"carlos"` with your target username.

---

## How the Bypass Works

```
Attempt 1:  carlos + password1  → 200  (counter: 1)
Reset:      wiener + peter      → 302  (counter: 0)
Attempt 2:  carlos + password2  → 200  (counter: 1)
Reset:      wiener + peter      → 302  (counter: 0)
...
```

Counter never reaches lockout threshold. All passwords testable.

---

## Difference From Previous Labs

| Lab | Bypass method |
|---|---|
| Multiple credentials per request | JSON array — 1 request, all passwords |
| IP block | Interleaved valid login — counter reset |
| X-Forwarded-For (timing lab) | Spoofed IP per request |

Three different rate-limit bypass techniques — same goal.

---

## Real Bug Bounty Application

1. Hit the limit on purpose — find the threshold (usually 3–10 attempts)
2. Log into your test account immediately — does the counter reset?
3. If yes — vulnerability confirmed
4. Report: show the counter resets, demonstrate all passwords testable
5. Never test on real users — use two accounts you own

---

## Usage

```bash
python3 ip-block-bypass.py
```

---

**Tags:** `#IPBlock` `#RateLimitBypass` `#BruteForce` `#Python` `#PortSwigger`
