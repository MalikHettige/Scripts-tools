#!/usr/bin/env python3
"""
Enrichment pattern: query an API (placeholder), normalize and save.
Replace API_KEY and endpoint with your provider (VirusTotal/Shodan).

Note: this is OSINT/domain-enrichment tooling, adjacent to but not part of
BAC/API/IDOR/auth/business-logic/race-condition hunting. Kept minimal on
purpose rather than built out further.
"""
import os
import sys
import json
import requests
from pathlib import Path

API_KEY = os.getenv("VT_API_KEY")
ENDPOINT = "https://www.virustotal.com/api/v3/domains/{}"
OUTDIR = Path("enrich_output")
OUTDIR.mkdir(exist_ok=True)


def enrich_domain(domain):
    if not API_KEY:
        sys.exit("Set the VT_API_KEY environment variable before running this script.")

    headers = {"x-apikey": API_KEY}
    r = requests.get(ENDPOINT.format(domain), headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
    else:
        data = {"error": {"status": r.status_code, "text": r.text}}

    summary = {
        "domain": domain,
        "last_analysis_stats": data.get("data", {}).get("attributes", {}).get("last_analysis_stats"),
        "whois": data.get("data", {}).get("attributes", {}).get("whois"),
    }
    out = OUTDIR / f"{domain}.json"
    out.write_text(json.dumps({"raw": data, "summary": summary}, indent=2))
    print(f"Saved {out}")
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: VT_API_KEY=xxx python enrich_example.py domain.com")
        sys.exit(2)
    print(enrich_domain(sys.argv[1]))