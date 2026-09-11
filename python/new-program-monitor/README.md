# VDP Finder

Finds newly-listed Vulnerability Disclosure Programs (VDPs) — non-paying
bug bounty programs — across HackerOne, Bugcrowd, and Intigriti.

## Why this exists

Freshly-listed VDP programs tend to have less-tested attack surface, since
fewer hunters have looked at them yet. Checking manually across three
platforms every day is tedious — this automates the "what's new" check.

## Data source

Pulls from [arkadiyt/bounty-targets-data](https://github.com/arkadiyt/bounty-targets-data),
a community-maintained mirror of all three platforms' program data,
refreshed every 30 minutes. This is used instead of hitting each
platform's own API directly, since those are undocumented, change without
notice, and require authentication this script doesn't use.

## What's reliable vs. what isn't

- **HackerOne** — fully classified. `offers_bounties: false` is a
  confirmed-reliable VDP indicator, verified against known real programs.
  `response_efficiency_percentage` is also real and populated — used for
  the `--min-efficiency` filter.
- **Bugcrowd** — no reliable field exists in this dataset to tell VDP from
  Paid. Every result is listed but flagged **UNVERIFIED** — cross-check
  each one against Bugcrowd's own [live filtered page](https://bugcrowd.com/engagements?category=vulnerability_disclosure_program)
  before spending hunting time on it.
- **Intigriti** — same situation as Bugcrowd, no confirmed classification
  field. Flagged **UNVERIFIED**, cross-check against the
  [live listings page](https://app.intigriti.com/researcher/programs).

Not fabricated/available from this dataset for any platform: resolved
report count, scope breadth, or general competition level. Always check
the program's own page before committing real hunting hours — including
on HackerOne, since a program can have `offers_bounties: false` and still
show an empty scope (not actually accepting reports yet).

## Usage

```bash
python vdp_finder.py                              # daily run, only new since last run
python vdp_finder.py --keyword api                # filter by keyword in name/handle
python vdp_finder.py --min-efficiency 80           # HackerOne only, response efficiency >= 80%
python vdp_finder.py --save results.txt            # write output to a file
python vdp_finder.py --force                       # run even on a weekend
python vdp_finder.py --reset-cache                 # ignore history, show everything again
```

Or double-click `run_vdp_finder.bat` for the daily default (saves to
`vdps.txt`, no flags).

## Weekend skip

Weekends are reserved for a separate smart-contract-security study track —
the script skips itself automatically on Saturday/Sunday. Use `--force`
to override.

## Files

- `vdp_finder.py` — the script
- `run_vdp_finder.bat` — double-click runner, Windows
- `seen_cache.json` — tracks what's already been shown (gitignored, local only)
- `results.txt` / `vdps.txt` — generated output (gitignored, local only)

## Known limitations

- "Newly launched" means *new to this tool's cache*, not necessarily
  freshly created by the platform — first run shows everything.
- The underlying dataset refreshes every 30 min; this script is only as
  current as that mirror.
- Bugcrowd/Intigriti sections require manual verification — see above.
