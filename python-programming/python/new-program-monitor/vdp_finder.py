#!/usr/bin/env python3
"""
vdp_finder.py

Fetches the newest VDP (Vulnerability Disclosure Program) listings from
HackerOne and Bugcrowd's public program directories and prints/saves links.

Usage:
    python vdp_finder.py
    python vdp_finder.py --save vdps.txt

Requires:
    pip install requests --break-system-packages
"""

import argparse
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install requests --break-system-packages")
    sys.exit(1)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
}


def fetch_hackerone_vdps(limit=25):
    """
    Pulls VDP-type programs from HackerOne's public directory API.
    Endpoint may change over time -- if this starts returning empty results,
    check https://hackerone.com/directory/programs in a browser and inspect
    the network tab for the current API shape.
    """
    url = "https://hackerone.com/graphql"
    query = {
        "operationName": "DirectoryQuery",
        "variables": {
            "first": limit,
            "query": "",
            "sort_type": "newest",
            "product_type": "VULNERABILITY_DISCLOSURE_PROGRAM",
        },
        "query": """
        query DirectoryQuery($first: Int, $query: String, $sort_type: String, $product_type: String) {
          teams(first: $first, query: $query, sort_type: $sort_type, product_type: $product_type) {
            edges {
              node {
                name
                handle
                url
              }
            }
          }
        }
        """,
    }

    results = []
    try:
        resp = requests.post(url, json=query, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        edges = data.get("data", {}).get("teams", {}).get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            handle = node.get("handle")
            if handle:
                results.append({
                    "name": node.get("name", handle),
                    "url": f"https://hackerone.com/{handle}",
                })
    except Exception as e:
        print(f"[HackerOne] Could not fetch via GraphQL ({e}). "
              f"Falling back to directory page link.")
        results.append({
            "name": "HackerOne VDP Directory (manual check)",
            "url": "https://hackerone.com/directory/programs?type=vdp&sort_type=newest",
        })

    return results


def fetch_bugcrowd_vdps(limit=25):
    """
    Pulls VDP-type programs from Bugcrowd's public engagements API.
    Bugcrowd doesn't have a stable public JSON API for this the way HackerOne
    does, so this hits their crowdstream/programs listing endpoint and falls
    back to a direct link to the filtered directory page if it fails.
    """
    url = "https://bugcrowd.com/engagements.json"
    params = {"category": "vulnerability_disclosure", "sort_by": "newest"}

    results = []
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        programs = data.get("engagements", []) or data.get("data", [])
        for p in programs[:limit]:
            name = p.get("name") or p.get("title")
            code = p.get("code") or p.get("brief_url") or p.get("slug")
            if name and code:
                results.append({
                    "name": name,
                    "url": f"https://bugcrowd.com/{code}",
                })
    except Exception as e:
        print(f"[Bugcrowd] Could not fetch via JSON endpoint ({e}). "
              f"Falling back to directory page link.")
        results.append({
            "name": "Bugcrowd VDP Directory (manual check)",
            "url": "https://bugcrowd.com/engagements?category=vulnerability_disclosure&sort_by=newest",
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch newest VDP program links.")
    parser.add_argument("--save", help="Save results to a text file", default=None)
    parser.add_argument("--limit", type=int, default=25, help="Max results per platform")
    args = parser.parse_args()

    print(f"Fetching newest VDPs... ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")

    h1 = fetch_hackerone_vdps(args.limit)
    bc = fetch_bugcrowd_vdps(args.limit)

    lines = []
    lines.append("=== HackerOne VDPs ===")
    for p in h1:
        lines.append(f"- {p['name']}: {p['url']}")

    lines.append("\n=== Bugcrowd VDPs ===")
    for p in bc:
        lines.append(f"- {p['name']}: {p['url']}")

    output = "\n".join(lines)
    print(output)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nSaved to {args.save}")


if __name__ == "__main__":
    main()
