#!/usr/bin/env python3
"""
Enrichment pattern: query an API (placeholder), normalize and save.
Replace API_KEY and endpoint with your provider (VirusTotal/Shodan).

Note: this is OSINT/domain-enrichment tooling, adjacent to but not part of
BAC/API/IDOR/auth/business-logic/race-condition hunting. Kept minimal on
purpose rather than built out further.
"""
import os
import re
import sys
import json
import time
from urllib.parse import quote

import requests
from pathlib import Path

API_KEY = os.getenv("VT_API_KEY")
ENDPOINT = "https://www.virustotal.com/api/v3/domains/{}"
OUTDIR = Path("enrich_output")

# Loose but strict-enough hostname check: labels of letters/digits/hyphens,
# dot-separated. Rejects path separators, whitespace, and anything else that
# could be used to escape OUTDIR or break the request path.
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)


def safe_filename(domain: str) -> str:
    """Build a filesystem-safe filename for `domain` with no traversal risk."""
    # Belt-and-braces even though validate_domain() already rejects anything
    # that isn't a bare hostname: strip any path separators before using the
    # value in a path, and fall back to a hash if nothing alnum is left.
    cleaned = re.sub(r"[^A-Za-z0-9.-]", "_", domain)
    cleaned = cleaned.strip(".")
    if not cleaned or cleaned in {".", ".."}:
        import hashlib
        cleaned = hashlib.sha256(domain.encode("utf-8")).hexdigest()
    return cleaned


def validate_domain(domain: str) -> str:
    domain = domain.strip()
    if not _DOMAIN_RE.match(domain):
        sys.exit(
            f"'{domain}' doesn't look like a bare hostname (e.g. example.com). "
            "Refusing to use it in a file path or API request."
        )
    return domain


def enrich_domain(domain, max_retries=3):
    if not API_KEY:
        sys.exit("Set the VT_API_KEY environment variable before running this script.")

    domain = validate_domain(domain)
    OUTDIR.mkdir(exist_ok=True)

    headers = {"x-apikey": API_KEY}
    url = ENDPOINT.format(quote(domain, safe=""))

    data = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=15)
        except requests.RequestException as exc:
            if attempt == max_retries:
                data = {"error": {"status": None, "text": f"request failed: {exc}"}}
                break
            time.sleep(2 ** attempt)
            continue

        if r.status_code == 200:
            data = r.json()
            break
        elif r.status_code == 429 and attempt < max_retries:
            # Rate-limited: back off and retry rather than silently recording a 429.
            retry_after = int(r.headers.get("Retry-After", 2 ** attempt))
            time.sleep(retry_after)
            continue
        else:
            data = {"error": {"status": r.status_code, "text": r.text}}
            break

    summary = {
        "domain": domain,
        "last_analysis_stats": data.get("data", {}).get("attributes", {}).get("last_analysis_stats"),
        "whois": data.get("data", {}).get("attributes", {}).get("whois"),
    }

    out = OUTDIR / f"{safe_filename(domain)}.json"
    # Defense in depth: even with validate_domain()/safe_filename() in place,
    # confirm the resolved path never escapes OUTDIR before writing.
    if OUTDIR.resolve() not in out.resolve().parents and out.resolve() != OUTDIR.resolve():
        sys.exit(f"Refusing to write outside {OUTDIR}: resolved to {out.resolve()}")
    out.write_text(json.dumps({"raw": data, "summary": summary}, indent=2))
    print(f"Saved {out}")
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: VT_API_KEY=xxx python enrich_example.py domain.com")
        sys.exit(2)
    print(enrich_domain(sys.argv[1]))
