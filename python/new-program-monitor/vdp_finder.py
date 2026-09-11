#!/usr/bin/env python3
"""
vdp_finder.py

Pulls program listings for HackerOne, Bugcrowd, and Intigriti from the
community-maintained "bounty-targets-data" project (hourly-updated,
3.9k+ stars, actively maintained as of this writing):
https://github.com/arkadiyt/bounty-targets-data

Features:
  - Skips weekends by default (use --force to run anyway)
  - Only shows programs not seen in a previous run (tracked in seen_cache.json)
  - Optional keyword filter (e.g. "api") to match your own hunting focus

Known limitations (being upfront rather than guessing):
  - Intigriti's raw data doesn't reliably expose a Paid/VDP flag in this
    dataset, so Intigriti entries are labeled "Program" (unclassified)
    rather than a guessed label that could be wrong.
  - Response efficiency (HackerOne) is NOT in this dataset - that metric
    lives in HackerOne's own directory UI, which doesn't have a stable
    public API. Not faked here; flagged as a manual check if you need it.

Usage:
    python vdp_finder.py
    python vdp_finder.py --save results.txt
    python vdp_finder.py --keyword api
    python vdp_finder.py --force          (run even on a weekend)
    python vdp_finder.py --reset-cache    (show everything again, ignore history)

Requires:
    pip install requests --break-system-packages
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install requests --break-system-packages")
    sys.exit(1)


BASE = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data"
SOURCES = {
    "HackerOne": f"{BASE}/hackerone_data.json",
    "Bugcrowd": f"{BASE}/bugcrowd_data.json",
    "Intigriti": f"{BASE}/intigriti_data.json",
}
CACHE_FILE = Path(__file__).parent / "seen_cache.json"


def fetch_json(url):
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def parse_hackerone(data):
    out = []
    for entry in data:
        handle = entry.get("handle")
        if not handle:
            continue
        offers_bounties = entry.get("offers_bounties")
        program_type = "VDP" if offers_bounties is False else (
            "Paid" if offers_bounties is True else "Unknown"
        )
        out.append({
            "name": entry.get("name", handle),
            "url": f"https://hackerone.com/{handle}",
            "type": program_type,
        })
    return out


def parse_bugcrowd(data):
    out = []
    for entry in data:
        name = entry.get("name")
        url_path = entry.get("url") or entry.get("briefUrl")
        if not name or not url_path:
            continue
        max_payout = entry.get("max_payout", 0) or 0
        program_type = "VDP" if max_payout == 0 else "Paid"
        full_url = url_path if url_path.startswith("http") else f"https://bugcrowd.com{url_path}"
        out.append({
            "name": name,
            "url": full_url,
            "type": program_type,
        })
    return out


def parse_intigriti(data):
    """
    Deliberately NOT guessing Paid vs VDP here - couldn't confirm the real
    field name, and a wrong label is worse than no label. Marked "Program"
    across the board until this is verified against live data.
    """
    out = []
    for entry in data:
        name = entry.get("name")
        handle = entry.get("handle") or entry.get("companyHandle")
        if not name:
            continue
        url = f"https://app.intigriti.com/programs/{handle}" if handle else "https://app.intigriti.com/researcher/programs"
        out.append({
            "name": name,
            "url": url,
            "type": "Program",
        })
    return out


PARSERS = {
    "HackerOne": parse_hackerone,
    "Bugcrowd": parse_bugcrowd,
    "Intigriti": parse_intigriti,
}


def load_cache():
    if CACHE_FILE.exists():
        try:
            return set(json.loads(CACHE_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_cache(urls):
    CACHE_FILE.write_text(json.dumps(sorted(urls)), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="List new programs across HackerOne, Bugcrowd, Intigriti.")
    parser.add_argument("--save", help="Save results to a text file", default=None)
    parser.add_argument("--keyword", help="Only show programs whose name contains this keyword (case-insensitive)", default=None)
    parser.add_argument("--force", action="store_true", help="Run even on a weekend")
    parser.add_argument("--reset-cache", action="store_true", help="Ignore previous run history, show everything")
    args = parser.parse_args()

    today = datetime.now()
    if today.weekday() >= 5 and not args.force:  # 5=Saturday, 6=Sunday
        print(f"Today is {today.strftime('%A')} - skipping (weekends reserved for smart contract study).")
        print("Run with --force if you want to check anyway.")
        return

    seen = set() if args.reset_cache else load_cache()
    new_seen = set(seen)

    lines = [f"Fetched {today.strftime('%Y-%m-%d %H:%M')} ({today.strftime('%A')})\n"]

    for platform, url in SOURCES.items():
        lines.append(f"=== {platform} ===")
        try:
            raw = fetch_json(url)
            parsed = PARSERS[platform](raw)

            if args.keyword:
                kw = args.keyword.lower()
                parsed = [p for p in parsed if kw in p["name"].lower()]

            new_entries = [p for p in parsed if p["url"] not in seen]

            if not parsed:
                lines.append("  (no programs parsed - dataset structure may have changed)")
            elif not new_entries:
                lines.append(f"  No new programs since last run ({len(parsed)} total, all previously seen)")
            else:
                for p in new_entries[:50]:
                    lines.append(f"  [{p['type']}] {p['name']}: {p['url']}")
                    new_seen.add(p["url"])

        except Exception as e:
            lines.append(f"  Failed to fetch/parse: {e}")
            lines.append(f"  Manual source: {url}")
        lines.append("")

    lines.append("Note: HackerOne response-efficiency filtering isn't available from this")
    lines.append("data source - check hackerone.com/directory manually if that matters for")
    lines.append("a specific program before committing hunting time to it.")

    output = "\n".join(lines)
    print(output)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nSaved to {args.save}")

    save_cache(new_seen)


if __name__ == "__main__":
    main()