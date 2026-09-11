# New Program Monitor (VDP)

Fetches and lists the newest Vulnerability Disclosure Programs (VDPs) from
HackerOne and Bugcrowd's public directories, so you don't have to manually
refresh-check for new targets.

## Why this exists

Freshly launched programs tend to have less-tested attack surface — fewer
hunters have looked at them yet. Checking manually every day is tedious;
this automates the "what's new" check.

## What it does

- Pulls newest VDP-type listings from HackerOne (via their GraphQL directory
  endpoint) and Bugcrowd (via their public engagements listing)
- Prints results to console, optionally saves to a text file
- Falls back to a direct link to each platform's filtered directory page if
  the API call fails — these platforms don't guarantee stable public APIs,
  so this tool is built to degrade gracefully instead of breaking silently

## Known limitations

- HackerOne and Bugcrowd can change their internal API structure at any
  time without notice. If this stops returning real results and just shows
  the fallback links, that's why — PRs welcome if you find the updated
  endpoint shape.
- This surfaces VDPs only, not paid bounty programs — by design.

## Setup

pip install requests --break-system-packages
python vdp_finder.py --save vdps.txt

Or on Windows, double-click run_vdp_finder.bat.

## Contributing

If HackerOne/Bugcrowd change their API and you find the fix, a PR with the
updated request shape is very welcome.
