#!/usr/bin/env python3
"""
vdp_finder.py — Finds newly-listed VDP (non-paying) bug bounty programs
across HackerOne, Bugcrowd, and Intigriti.

Data source: https://github.com/arkadiyt/bounty-targets-data
(community-maintained, refreshed every 30 min)

Usage:
    python vdp_finder.py --keyword api --save results.txt
    python vdp_finder.py --save results.txt
    python vdp_finder.py --force
    python vdp_finder.py --reset-cache --save results.txt
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_FILE = SCRIPT_DIR / "seen_cache.json"

HACKERONE_URL = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/hackerone_data.json"
BUGCROWD_URL = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/bugcrowd_data.json"

BUGCROWD_LIVE_PAGE = "https://bugcrowd.com/engagements?category=vulnerability_disclosure_program"
INTIGRITI_LIVE_PAGE = "https://app.intigriti.com/researcher/programs"


def fetch_json(url: str):
    """Fetch and parse JSON from a URL. Returns None on failure (does not crash)."""
    try:
        req = Request(url, headers={"User-Agent": "vdp_finder/1.0"})
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, TimeoutError) as e:
        print(f"  [!] Failed to fetch {url}: {e}")
        return None


def load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {"hackerone": [], "bugcrowd": []}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"hackerone": [], "bugcrowd": []}


def save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def get_hackerone_vdps(keyword: str | None) -> list[dict]:
    """
    HackerOne: offers_bounties is the only confirmed-reliable classification
    field. offers_bounties == False means VDP (no bounty).
    """
    data = fetch_json(HACKERONE_URL)
    if data is None:
        return []

    results = []
    for program in data:
        if program.get("offers_bounties") is True:
            continue  # paid program, skip — VDP only

        name = program.get("name", "Unknown")
        handle = program.get("handle", "")
        url = program.get("url", f"https://hackerone.com/{handle}")

        if keyword and keyword.lower() not in name.lower() and keyword.lower() not in handle.lower():
            continue

        results.append({
            "platform": "HackerOne",
            "name": name,
            "handle": handle,
            "url": url,
        })

    return results


def get_bugcrowd_listing(keyword: str | None) -> list[dict]:
    """
    Bugcrowd: no reliable field to auto-classify VDP vs Paid from this
    dataset (max_payout is NOT reliable — see brief). We list programs from
    the dataset for the "new program" diff mechanism, but flag every entry
    as UNVERIFIED VDP status — cross-check manually against Bugcrowd's own
    live-filtered VDP page before spending hunting time on it.
    """
    data = fetch_json(BUGCROWD_URL)
    if data is None:
        return []

    results = []
    for program in data:
        name = program.get("name", "Unknown")
        code = program.get("code", "")
        url = program.get("url", f"https://bugcrowd.com/{code}")

        if keyword and keyword.lower() not in name.lower() and keyword.lower() not in code.lower():
            continue

        results.append({
            "platform": "Bugcrowd",
            "name": name,
            "handle": code,
            "url": url,
        })

    return results


def diff_against_cache(programs: list[dict], cache_key: str, cache: dict) -> list[dict]:
    seen = set(cache.get(cache_key, []))
    new_programs = [p for p in programs if p["handle"] not in seen]
    # update cache with everything seen this run
    cache[cache_key] = list(seen | {p["handle"] for p in programs})
    return new_programs


def format_output(h1_new, bc_new, reset_cache: bool) -> str:
    lines = []
    lines.append(f"VDP Program Monitor — run at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)

    tag = "ALL (cache reset)" if reset_cache else "NEW SINCE LAST RUN"

    lines.append(f"\n--- HackerOne VDPs [{tag}] — fully classified via offers_bounties ---")
    if h1_new:
        for p in h1_new:
            lines.append(f"  {p['name']}")
            lines.append(f"    {p['url']}")
    else:
        lines.append("  (none new)")

    lines.append(f"\n--- Bugcrowd listings [{tag}] — UNVERIFIED VDP status, check manually ---")
    lines.append(f"  Cross-check against live filtered page: {BUGCROWD_LIVE_PAGE}")
    if bc_new:
        for p in bc_new:
            lines.append(f"  {p['name']}")
            lines.append(f"    {p['url']}")
    else:
        lines.append("  (none new)")

    lines.append(f"\n--- Intigriti ---")
    lines.append("  Not auto-classified — field names for Paid/VDP status were never")
    lines.append("  confirmed from this dataset. Check live listings directly:")
    lines.append(f"  {INTIGRITI_LIVE_PAGE}")

    lines.append(f"\n--- Known limitations (not fabricated, deliberately omitted) ---")
    lines.append("  Response efficiency, resolved-report count, and competition level")
    lines.append("  are NOT available from this dataset. Check each program's own")
    lines.append("  dashboard page manually before committing hunting hours.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Find newly-listed VDP programs.")
    parser.add_argument("--keyword", help="Filter results by keyword in program name/handle")
    parser.add_argument("--save", metavar="FILE", help="Save output to a text file")
    parser.add_argument("--force", action="store_true", help="Run even on a weekend")
    parser.add_argument("--reset-cache", action="store_true", help="Ignore history, show everything again")
    args = parser.parse_args()

    if datetime.now().weekday() >= 5 and not args.force:
        print("Today is a weekend — smart-contract-security study day, skipping VDP scan.")
        print("Use --force to run anyway.")
        sys.exit(0)

    cache = {"hackerone": [], "bugcrowd": []} if args.reset_cache else load_cache()

    print("Fetching HackerOne data...")
    h1_all = get_hackerone_vdps(args.keyword)
    print("Fetching Bugcrowd data...")
    bc_all = get_bugcrowd_listing(args.keyword)

    h1_new = diff_against_cache(h1_all, "hackerone", cache)
    bc_new = diff_against_cache(bc_all, "bugcrowd", cache)

    save_cache(cache)

    output = format_output(h1_new, bc_new, args.reset_cache)
    print("\n" + output)

    if args.save:
        save_path = Path(args.save)
        save_path.write_text(output, encoding="utf-8")
        print(f"\n[Saved to {save_path}]")


if __name__ == "__main__":
    main()
