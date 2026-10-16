# Triage & report drafting

Takes raw output from [`recon/`](../recon/README.md) tooling (or any similarly-shaped `httpx`/`katana`/fuzz output), scores and dedupes it into a single prioritized findings list, and drafts Markdown report stubs from it. This is the stage *after* recon, not recon itself — it doesn't do any discovery of its own.

**Pipeline:** `recon/*` output → `triage.py` → `findings.jsonl` → `reportgen.py` → Markdown report draft.

## `triage.py`

Normalizes, dedupes, and scores recon output from multiple sources into one findings list.

```bash
python triage.py \
  --live recon-target/live.txt \
  --crawled recon-target/crawled-urls.txt \
  --fuzz recon-target/fuzz-results.txt \
  --output recon-target/findings.jsonl \
  --csv recon-target/findings.csv

# or auto-discover inputs by filename pattern in a directory
python triage.py --dir recon-target/ --output findings.jsonl --csv findings.csv
```

- Accepts `httpx -title` live-host output, `katana`/generic crawled URL lists, and dirfuzz-style `STATUS LENGTH URL` lines (what `recon/async_dirfuzz.py` produces) — plus raw JSONL/ffuf-JSON as direct input.
- `--dir` auto-discovers input files by filename heuristics (`live`, `crawl`/`urls`/`links`, `fuzz`/`result`/`dir`/`.jsonl`/`.json`) instead of naming each one explicitly.
- Scores each URL using path/status/title heuristics (admin-like paths, exposed API docs, leaked config/backup files, auth-protected responses, etc.) and buckets into `critical`/`high`/`medium`/`low`/`info`.
- Dedupes by URL fingerprint (SHA-256 of the normalized URL), merging repeated sightings and keeping the higher score.
- Persists to a SQLite DB (`--db`, default `triage.db`) in addition to JSONL/CSV output, so repeated runs against the same target accumulate state rather than overwrite it.
- CSV output is formula-injection-safe — values starting with `=`, `+`, `-`, `@` are prefixed to prevent them executing as formulas when opened in Excel/Sheets (titles are scraped, attacker-influenced content).
- `--min-score` filters out low-value noise from the output.

No external dependencies — standard library only.

## `reportgen.py`

Drafts a Markdown report from `triage.py`'s `findings.jsonl`, either for one specific finding or a top-N summary.

```bash
# One specific finding, by fingerprint, index, or URL
python reportgen.py --input findings.jsonl --id <fingerprint> --output report.md

# Highest-scored finding if no --id given
python reportgen.py --input findings.jsonl --output report.md

# Summary of the top N findings
python reportgen.py --input findings.jsonl --top 5 --output report.md
```

- Renders via `report_template.j2` (Jinja2) sitting alongside the script — don't move one without the other, or pass `--template` explicitly to point at wherever it actually is.
- `--stdout` also prints the generated Markdown to the terminal, in addition to writing the file.
- The verification command included in each single-finding report (`curl ... -w 'HTTP %{http_code}'`) is shell-escaped against the finding's URL — URLs come from scraped/fuzzed content, so this matters if you're going to copy-paste it straight into a terminal.
- Output is a draft, not a final report — it's meant to save the repetitive boilerplate writing, with a human still reviewing and editing before anything gets submitted.

Dependencies: `jinja2`

## Notes

- Both scripts were verified end-to-end against synthetic recon output before being documented here — `triage.py` correctly parses/scores/dedupes mixed `live`/`crawled`/`fuzz` input, and `reportgen.py` correctly renders both single-finding and `--top` summary reports from its output.
- `report_template.j2` is required for `reportgen.py` to run without `--template` — if it's ever missing, regenerate or restore it rather than leaving the script broken.
