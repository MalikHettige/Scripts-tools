# Tools built for recon

Small, standalone recon tools used ahead of/alongside manual hunting. Not vulnerability-specific — this is infrastructure that feeds into the actual vuln-class work tracked elsewhere in this repo.

Output from these tools feeds into [`triage/`](../triage/README.md), which dedupes, scores, and drafts reports from whatever gets found here.

## Scripts

### `subagg.py`
Passive subdomain aggregator. Queries crt.sh (certificate transparency) and, optionally, VirusTotal, OTX, and local `amass`/`subfinder` binaries, then merges and dedupes everything into one canonical domain list scoped to the target apex.

```bash
python subagg.py example.com
python subagg.py example.com -o out/ --amass --subfinder
VT_API_KEY=xxx OTX_API_KEY=yyy python subagg.py example.com --vt --otx
```

- Core path (crt.sh) needs no API key and no extra packages — runs on the standard library alone (`requests` is used automatically if installed, but isn't required).
- `--vt`/`--otx` are opt-in and need `VT_API_KEY`/`OTX_API_KEY` set as environment variables; missing either just skips that source with a warning, it doesn't hard-fail.
- `--amass`/`--subfinder` run the local binary in passive mode if it's on `PATH`; skipped with a warning if not installed.
- Every source degrades independently — one failing (network error, missing key, missing binary) doesn't stop the others. The run only fails if *every* source comes back empty.
- Output is scoped: anything not equal to or a subdomain of the target apex is filtered out, so noise from crt.sh (which commonly returns unrelated domains sharing a cert) doesn't leak through.
- Writes `domains.txt` (plain sorted list, feed straight into `async_dirfuzz.py` or `triage.py`) and `domains.jsonl` (`{"domain": ..., "sources": [...]}`, keeping which source(s) found each host).
- Parsing/dedup logic verified against synthetic crt.sh/VirusTotal/OTX/amass-shaped sample data, plus CLI error-path checks (invalid domain, all-sources-unreachable) — all passed before being documented here.

#### Just want one result? (no repo, no setup)

```bash
curl -o subagg.py "https://raw.githubusercontent.com/MalikHettige/scripts-tools/main/recon/subagg.py"
python3 subagg.py example.com
```

Delete `subagg.py` afterward if you don't need it again.

<img width="1335" height="405" alt="image" src="https://github.com/user-attachments/assets/f4c21b19-88d9-4adb-863a-1e1ae7686ac1" />

#### Frequent use (clone and keep)

```bash
git clone https://github.com/MalikHettige/scripts-tools.git "$HOME/GitHub/Scripts-tools"
```

Then, from anywhere:

```bash
python3 ~/GitHub/Scripts-tools/recon/subagg.py example.com
```

Dependencies: none required (standard library only); `requests` optional for nicer error handling.

### `monitor.py`
Continuous delta watcher / asset monitor. Takes a domain list (e.g. `subagg.py`'s `domains.jsonl`) and compares it against history stored in SQLite, reporting what's genuinely new or dropped since the last run for that target — built to be run repeatedly (cron, GitHub Actions) against the same target over time.
 
```bash
python monitor.py --input domains.jsonl --target example.com
python monitor.py --input domains.jsonl --target example.com --db history.db
python monitor.py --input domains.jsonl --target example.com --slack-webhook "$SLACK_WEBHOOK_URL"
python monitor.py --input domains.jsonl --target example.com --github-repo MalikHettige/scripts-tools --github-token "$GITHUB_TOKEN"
```
 
- First run against a target is treated as a baseline (seeds history, nothing alert-worthy yet) — every run after that reports real deltas.
- Diffing is against the *previous run's* snapshot, not the all-time ledger — a domain that drops once is reported once, not re-flagged on every subsequent run forever (a real bug caught and fixed during testing: an earlier version diffed against the full historical "ever seen" set, which meant anything that ever disappeared stayed permanently flagged as "dropped").
- A separate historical ledger (`seen_domains`, with `first_seen`/`last_seen`) is still kept alongside the snapshot, so you can see when something was first spotted even though diffing doesn't use it.
- Accepts either `domains.jsonl` (subagg.py's shape) or a plain `domains.txt` as input.
- `--slack-webhook` (or `SLACK_WEBHOOK_URL` env var) posts a plain-text alert on any delta; `--github-repo` + `--github-token` (or `GITHUB_TOKEN` env var) opens a GitHub issue instead/as well. Both are optional and skip silently with a warning if not configured.
- `--quiet` suppresses the printed summary without affecting alerts.
- History (`--db`, default `monitor.db`) is scoped per `--target`, so multiple targets can share one DB file without cross-contaminating each other's baselines.
- Verified end-to-end: baseline run, delta run (new + dropped), no-change run, and a dropped-domain-reappears run — including the regression case for the snapshot-vs-ledger bug above — plus error paths (missing input file, unparseable input).
#### Just want one result? (no repo, no setup)
 
```bash
curl -o monitor.py "https://raw.githubusercontent.com/MalikHettige/scripts-tools/main/recon/monitor.py"
python3 monitor.py --input domains.jsonl --target example.com
```
 
Delete `monitor.py` (and `monitor.db`, if you don't want to keep the history) afterward if you don't need it again.
 
#### Frequent use (clone and keep)
 
```bash
git clone https://github.com/MalikHettige/scripts-tools.git "$HOME/GitHub/Scripts-tools"
```
 
Then, from anywhere:
 
```bash
python3 ~/GitHub/Scripts-tools/recon/monitor.py --input domains.jsonl --target example.com
```
 
Dependencies: none required (standard library only — `sqlite3`, `json`, `urllib`); `requests` optional for nicer error handling on the Slack/GitHub alert calls.
