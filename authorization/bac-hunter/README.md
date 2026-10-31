# bac-hunter

Automated broken-access-control (BAC) testing from a captured traffic
export. Takes requests you've already seen in Burp/ZAP, replays each
identifier-bearing endpoint under every configured session, and under
swapped object IDs within the same session, then flags responses that look
like they leaked data they shouldn't have. Output is a ranked markdown or
JSON report with the exact request/response pairs, so you can verify fast
and write up.

**This tool flags anomalies. It does not confirm exploitability.** Every
finding needs a manual look before you report it. Use only against targets
you are explicitly authorized to test, and keep concurrency/delay within
whatever rate limits the program sets.

## What it does

1. Parses a Burp "save items" XML export, an OWASP ZAP export (XML or
   JSON), or a plain-text request list, into a list of requests.
2. Extracts every parameter that looks like an object/user/org identifier
   — by name (`user_id`, `account_id`, `order_id`, ...) or by shape (UUID,
   Mongo ObjectId, bare numeric ID) — from the query string, path
   segments, JSON body, form body, and a few common identifier headers.
3. For each candidate, runs the configured mutation strategies:
   - **session_swap**: same object ID, every OTHER configured session's
     auth. Catches horizontal IDOR (peer user's object) and vertical
     privilege escalation (lower-level session reaching a higher-level
     object), depending on how you set session `level`.
   - **object_id_swap**: same session's own auth, object ID swapped to
     another known ID (declared in config) or a numeric neighbor
     (`id±1`, lower confidence, flagged for manual check since a
     neighboring ID might not even exist).
4. Sends everything concurrently via `aiohttp`, bounded by `--concurrency`.
5. Diffs each mutated response against a cached baseline (status, body
   length, byte-for-byte body match) and flags anything that smells like
   broken access control — ranked high/medium/low confidence.
6. Writes a markdown or JSON report with every flagged request/response
   pair in full.

**Not included:** automated JWT `kid`/`jku` header forgery. Forging a JWT
and mass-testing it against every endpoint is a different category of tool
from authorized BAC replay, so it's left out here. The mutation-strategy
interface (`bac_hunter/mutations/base.py`) is there if you want to test
JWT handling yourself, one request at a time, against a target you control.

## Install

```bash
cd bac-hunter
pip install -r requirements.txt
# or: pip install --break-system-packages -r requirements.txt   (Linux VM, no venv)
```

Python 3.10+. No separate install step needed beyond the deps — run it as
a module (`python3 -m bac_hunter.cli ...`), or `pip install -e .` for the
`bac-hunter` console command.

## Usage

```bash
python3 -m bac_hunter.cli \
  --input traffic.xml \
  --sessions sessions.json \
  --out report.md
```

### Input formats (`--input`)

- **Burp**: Proxy/Target → right-click → "Save selected items" → XML, with
  base64-encoded requests (the default).
- **ZAP**: Report → Generate Report (XML/JSON with alert items), or an
  export containing `requestHeader`/`requestBody` per message. ZAP's export
  shapes vary by version/add-on — if yours doesn't parse, save requests as
  raw text instead (see below) or export as HAR and convert.
- **Raw text**: either one `METHOD URL` per line —
  ```
  GET https://target.com/api/orders/1001
  POST https://target.com/api/orders  Content-Type: application/json
  ```
  — or full raw HTTP request blocks (as copied from Burp's "Copy as
  request"), separated by a line of `---`:
  ```
  GET /api/orders/1001 HTTP/1.1
  Host: target.com
  Cookie: session=abc123

  ---
  POST /api/orders HTTP/1.1
  Host: target.com
  Content-Type: application/json

  {"order_id": 1001}
  ```
- **JSON request list**: `[{"method": "GET", "url": "...", "headers": {...}, "body": null}, ...]`

### Session config (`--sessions`)

JSON or YAML, at least 2 sessions. `level` controls escalation direction in
reports (lower = less privileged) — set both to the same value for a pure
horizontal (peer-to-peer) test.

```json
{
  "sessions": [
    {
      "name": "low_priv_user",
      "level": 0,
      "cookie": "session=abc123; other=xyz",
      "object_ids": ["1002", "a1b2c3d4-..."]
    },
    {
      "name": "admin_user",
      "level": 1,
      "bearer": "eyJhbGciOi...",
      "headers": {"X-Org-Id": "org_42"},
      "object_ids": ["1001"]
    }
  ]
}
```

- `cookie` and/or `bearer` replace whatever `Cookie`/`Authorization` the
  captured request had.
- `headers` adds/overrides any other header (e.g. a custom org-scoping
  header some APIs use alongside the session token).
- `object_ids` are optional: IDs you know belong to *this* session (your
  own user ID, an order you placed, etc). `object_id_swap` uses these as
  high-confidence replacement values instead of guessing numeric neighbors.
  Fill these in from your own two test accounts for much better signal.

### Strategies, concurrency, output

```bash
python3 -m bac_hunter.cli \
  --input traffic.xml --sessions sessions.json \
  --strategies session_swap object_id_swap \
  --concurrency 8 --delay 0.2 \
  --timeout 20 \
  --out report.json --format json \
  --target-label "AcmeCorp - Orders API"
```

| Flag | Default | Notes |
|---|---|---|
| `--strategies` | all registered | space-separated list |
| `--concurrency` | 10 | raise for speed, lower to stay under a program's rate limit |
| `--delay` | 0 | seconds to sleep after each request; combine with low `--concurrency` for strict rate limits |
| `--timeout` | 15 | per-request seconds |
| `--max-requests` | unlimited | cap candidate params tested, for a quick pass |
| `--insecure` | off | skip TLS verification (self-signed lab targets) |
| `--format` | inferred from `--out` extension | `markdown` or `json` |

## Demo / self-test

A tiny local target is included with one correctly-protected endpoint and
one with a deliberately missing ownership check, so you can see the tool
catch a real bug and *not* flag the safe one:

```bash
python3 tests/mock_server.py &        # serves on 127.0.0.1:8765
python3 -m bac_hunter.cli \
  --input tests/requests.txt \
  --sessions tests/sessions.json \
  --out /tmp/demo-report.md
cat /tmp/demo-report.md
```

`/api/orders/<id>` checks ownership properly → no finding.
`/api/invoices/<id>` has no ownership check → flagged HIGH by `session_swap`.

## Reading the report

Every finding shows the baseline (the request as originally captured) and
the mutated request/response that got flagged, in full, inside collapsible
`<details>` blocks. Confidence levels:

- **high** — baseline was denied (401/403/404) and the mutation got 200
  with data, OR the mutated response body is byte-identical to a baseline
  that belongs to a different identity/object (both are strong signals).
- **medium** — baseline returned an empty 200 and the mutation returned
  data, or similar partial signals.
- **low** — both requests "succeeded" but body sizes differ meaningfully;
  could easily be legitimate different data — verify by hand before you
  trust it.

False positives happen (pagination, timestamps, and per-request nonces in
response bodies all throw off the length/byte-diff heuristics). False
negatives happen too — an endpoint that returns identical, generic
"success" responses regardless of identity, with no real per-object
content, won't diff as suspicious even if it's broken. This tool narrows
where you look; it doesn't replace reading the response.

## Extending: adding a new mutation strategy

Strategies are plugins. Drop a new file in `bac_hunter/mutations/`,
subclass `MutationStrategy`, implement `async def run(self, candidate,
ctx) -> list[Finding]`, and register it in
`bac_hunter/mutations/__init__.py`'s `STRATEGIES` dict. You get:

- `candidate.request` / `candidate.location` — the source request and
  which param was picked out (query/path/json_body/form_body/header).
- `ctx.sessions` — all configured sessions.
- `ctx.client.send(req)` — send any `HttpRequest`, async, through the
  shared connection pool/semaphore.
- `ctx.baseline_cache` — shared across strategies so you don't refire the
  same baseline request twice; key however you like.
- `bac_hunter.rebuild.with_param_value(req, loc, new_value)` — clone a
  request with one candidate param's value swapped, wherever it lives.
- `MutationStrategy.is_suspicious(baseline, mutated)` — the shared
  anomaly heuristic, or write your own from scratch.

```python
# bac_hunter/mutations/my_strategy.py
from .base import MutationStrategy, MutationContext
from ..models import CandidateParam, Finding

class MyStrategy(MutationStrategy):
    name = "my_strategy"

    async def run(self, candidate: CandidateParam, ctx: MutationContext) -> list[Finding]:
        ...
```

```python
# bac_hunter/mutations/__init__.py
from .my_strategy import MyStrategy
STRATEGIES["my_strategy"] = MyStrategy
```

It'll show up automatically in `--strategies` choices.

## Project layout

```
bac_hunter/
  cli.py            entry point / argument parsing
  engine.py          parse -> extract -> strategies -> findings
  models.py           HttpRequest/HttpResponse/CandidateParam/Finding
  extract.py          identifier-param discovery
  rebuild.py           swap one param's value back into a request
  client.py             async HTTP layer (aiohttp, bounded concurrency)
  sessions.py           session/privilege-level config loader
  report.py              markdown/JSON report rendering
  parsers/
    burp.py               Burp XML export
    zap.py                 ZAP XML/JSON export
    raw.py                  plain-text / raw HTTP / JSON request list
  mutations/
    base.py                 MutationStrategy ABC + shared anomaly heuristic
    session_swap.py          strategy 1
    object_id_swap.py        strategy 2
tests/
  mock_server.py             local demo target (one safe endpoint, one buggy)
  sessions.json / requests.txt    demo config/input
```
