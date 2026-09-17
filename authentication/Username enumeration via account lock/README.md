# Username Enumeration via Account Lock

## Tools & Approaches

| Tool              | Pros                              | Cons                          | Best For                  |
|-------------------|-----------------------------------|-------------------------------|---------------------------|
| Burp Intruder     | Precise control                   | Very slow (Community)         | Learning / small lists    |
| ffuf              | Fast                              | Needs careful payload setup   | Quick testing             |
| Python + requests | Full control, easy logging        | Requires scripting            | Reliable automation       |
| Turbo Intruder    | Extremely fast                    | Steeper learning curve        | Large attacks             |

---

## Recommended Detection Logic (Python)

```python
if response.status_code == 302:
    # Strong success indicator
elif "too many incorrect" in response.text.lower():
    # Valid username found (lockout triggered)
elif "Invalid username or password" not in response.text:
    # Possible success or interesting behavior
