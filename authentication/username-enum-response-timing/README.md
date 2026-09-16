# Username Enumeration via Response Timing

> Scripts used to solve the PortSwigger lab: **Username enumeration via response timing**  
> Detects valid usernames by measuring bcrypt execution time difference. Bypasses IP rate limiting via X-Forwarded-For spoofing.

---

## Directory Structure

```
username-enum-response-timing/
├── README.md
├── username-enum-timing.py    # Phase 1: timing attack to find valid username
└── password-brute.py          # Phase 2: brute-force with IP rotation
```

---

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

---

## Why This Is Harder Than Previous Labs

| Lab | Signal | Detectable by |
|---|---|---|
| Different responses | Error message text | Eyes / Burp |
| Subtly different | Trailing space | Python string check |
| Response timing | Milliseconds | Python timer only |

No visual difference. No byte difference. Pure time measurement.

---

## Why Two Scripts

**Phase 1** runs 3 timed requests per username and averages them — reduces network jitter. Sorts all results by slowest. The outlier is the valid username.

**Phase 2** brute-forces the confirmed username with a rotating `X-Forwarded-For` IP per request to bypass the rate limiter.

---

## The X-Forwarded-For Bypass

The app rate-limits by IP using the `X-Forwarded-For` header — which is spoofable:

```python
fake_ip = f"192.168.{i // 256}.{i % 256}"
headers = {"X-Forwarded-For": fake_ip}
```

Each request appears to come from a different IP. Rate limiter never triggers.

**Also try on real targets:** `X-Real-IP`, `X-Client-IP`, `True-Client-IP`

---

## Usage

```bash
# Phase 1 — find valid username via timing
python3 username-enum-timing.py

# Phase 2 — brute-force password (edit username first)
python3 password-brute.py
```

---

**Tags:** `#TimingAttack` `#XForwardedFor` `#RateLimitBypass` `#Python` `#PortSwigger`
