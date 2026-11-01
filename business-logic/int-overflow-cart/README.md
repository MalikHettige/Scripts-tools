# int-overflow-cart

Automates integer-overflow price manipulation in e-commerce cart/quantity endpoints that compute `total = quantity × unit_price` server-side using a fixed-width signed integer with no bounds checking on the result.

## What it does

1. Sends repeated add-to-cart requests to inflate quantity toward the point where `quantity × unit_price` exceeds the integer's max value and wraps to a negative (or small) number.
2. Parses the live `/cart` total after each request instead of guessing blind — Phase 1 runs coarse batches, Phase 2 switches to 1-unit steps once it's close to the crossing point.
3. Auto-stops the moment the total lands inside a target window (default `$0–$100`) instead of requiring manual monitoring.
4. **Never auto-places the order.** Checkout is always a manual, deliberate step — on a lab or a real target.

## When this technique applies

- Quantity has a per-request server-side cap (not just client-side/HTML `maxlength`) — confirmed via a 400 on an oversized value.
- Price is never a directly editable parameter; it's always calculated server-side from quantity × unit price.
- The server does the multiplication without checking for overflow before using the result in a balance/total comparison.

If quantity rejects at literally any value above 1, or price *is* a directly editable field, this is a different bug class — don't force this script onto it.

## Setup — fill in 5 values

Open `overflow_exploit.py` and set:

| Variable          | Where to get it                                      |
|--------------------|-------------------------------------------------------|
| `TARGET`           | Base URL of the target, e.g. `https://shop.example.com` |
| `SESSION_COOKIE`   | Pull from DevTools / Burp after logging in            |
| `HOST_VALUE`        | Cookie domain, usually same host as TARGET            |
| `PRODUCT_ID`        | Confirm via Burp — don't assume product order/index    |
| `UNIT_PRICE`        | Read off the product page, exact value                |

## Confirm 2 values in Burp before running

These can't be known in advance — test them manually first:

1. **`MAX_QTY_PER_REQUEST`** — in Burp Repeater, try `quantity=999`, then binary-search down until you find the highest value that returns 200 instead of a 400. Default assumption is `99`.
2. **`INT_WIDTH`** — default `32`. Can't be tested directly; if the total never overflows near the 32-bit threshold after the calculated batch count runs, the backend is likely 64-bit (not practically exploitable via request volume) or there's a separate validation layer catching it.

## Running it

```bash
pip install requests --break-system-packages   # if not already installed
python overflow_exploit.py
```
- Create a nano file and paste the script
```bash
nano overflow.py
#paste the script
```
- **Ctrl + O**
- **Hit enter**
- **Ctrl + X**
- Then run `python overflow.py`

The script prints its calculated overflow target and batch estimate, then gives you 5 seconds to Ctrl+C if the numbers look wrong before it starts firing requests.

## Real-world usage rules

- Only run against **in-scope** targets under an active bug bounty / VDP engagement. Check the program's policy for automation/rate-limit rules before running unthrottled.
- **Stop at proof, not profit.** Once the total lands in the target window, screenshot it and write the report. Do not click "place order" to actually receive the item — that crosses from vulnerability research into fraud.
- Throttle (`time.sleep`) is included by default; only remove it if a program's scope explicitly allows high-rate automated testing.
- The `/cart` HTML parsing regex is written for PortSwigger lab markup. On a real target, test the regex against a plain `GET /cart` response first — different sites render totals differently and the auto-stop will silently fail to trigger if the pattern doesn't match.

## Origin

Built and tested against PortSwigger Web Security Academy — *Business logic vulnerabilities* → **Low-level logic flaw** lab.
