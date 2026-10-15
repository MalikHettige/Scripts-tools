# Tools built for recon 

Small, standalone recon tools used ahead of/alongside manual hunting. Not vulnerability-specific — this is infrastructure that feeds into the actual vuln-class work tracked elsewhere in this repo.

## Scripts

### `async_dirfuzz.py`
Async directory/file content discovery against a target host.

```bash
python async_dirfuzz.py target.com wordlist.txt
python async_dirfuzz.py target.com wordlist.txt --ext json,bak,old,swp -o results.txt -c 30 -t 8
```

- Auto-calibrates against soft-404 responses before the real sweep (apps that return `200 OK` with a custom "not found" page instead of a real 404) so those don't flood results as false positives.
- `--ext` appends extensions per wordlist entry — useful for sweeping leaked config/spec files (`openapi.json`, `.bak`, `.old`) alongside plain paths.
- `-o` writes matches to a file in addition to stdout; without it, results only print live.
- Redirects (301/302/307/308) are flagged distinctly from real 200-class hits rather than lumped together.
- Tested locally against a mock server simulating a soft-404 trap — confirmed the calibration step correctly filters noise that a naive status-only check would report as 100% false positives. See `/writeups` methodology notes for the before/after.

Dependencies: `aiohttp`

### `enrich_example.py`
Domain OSINT/enrichment via VirusTotal's public API.

```bash
VT_API_KEY=xxx python enrich_example.py domain.com
```

- Requires `VT_API_KEY` set as an environment variable — the script exits cleanly with a clear message if it's missing, rather than silently firing a request with an invalid key.
- Saves both the raw API response and a normalized summary (analysis stats, whois) to `enrich_output/<domain>.json`.
- Adjacent tooling, not core to the BAC/API/IDOR/auth/business-logic/race-condition hunting lane this repo is otherwise built around — used situationally during initial target recon, not a standing part of the usual flow.

Dependencies: `requests`

## Notes

- These are intentionally minimal, single-purpose scripts, not a framework — extend in place rather than refactoring into a shared module unless a third script actually needs to share logic with one of these.
- More scripts will likely land here over time (subdomain enumeration, JS endpoint extraction, parameter discovery, etc.) as the recon workflow in the main methodology grows past what manual Burp work covers efficiently. Each new addition should stay standalone and get its own section in this README, same format as above — command, what it filters/flags, dependencies, and a one-line scope note on where it fits (or doesn't) relative to the core vuln-class focus.
