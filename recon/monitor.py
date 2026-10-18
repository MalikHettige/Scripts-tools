#!/usr/bin/env python3
"""
monitor.py — continuous delta watcher / asset monitor

Takes a domain list (from subagg.py's domains.jsonl/domains.txt, or any
newline-delimited hostname file), compares it against what's been seen
before for that target, and reports what's new (and, optionally, what
dropped off). Designed to be run on a schedule (cron, GitHub Actions)
against the same target repeatedly — each run accumulates history in a
local SQLite DB rather than starting fresh.

Usage:
    python monitor.py --input domains.jsonl --target example.com
    python monitor.py --input domains.txt --target example.com --db history.db
    python monitor.py --input domains.jsonl --target example.com \
        --slack-webhook "$SLACK_WEBHOOK_URL"
    python monitor.py --input domains.jsonl --target example.com \
        --github-repo MalikHettige/scripts-tools --github-token "$GITHUB_TOKEN"

First run against a target just seeds history (everything looks "new" —
that's expected and gets labeled as a baseline run, not an alert-worthy
delta). Every run after that reports genuine deltas.

No required third-party deps — stdlib only (sqlite3, json, urllib). Slack
webhook posting and GitHub issue creation use `requests` if available,
falling back to urllib otherwise.
"""

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$"
)


def normalize_domain(raw: str) -> str | None:
    if not raw:
        return None
    d = raw.strip().lower().rstrip(".")
    if d.startswith("*."):
        d = d[2:]
    if not d or " " in d:
        return None
    if not HOSTNAME_RE.match(d):
        return None
    return d


def load_domains(path: Path) -> set[str]:
    """Load domains from a .jsonl file (subagg.py's domains.jsonl shape,
    {"domain": "...", ...} per line) or a plain newline-delimited .txt file.
    Falls back to line-based parsing for any other extension."""
    text = path.read_text()
    domains: set[str] = set()
    if path.suffix == ".jsonl":
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = normalize_domain(row.get("domain", "")) if isinstance(row, dict) else None
            if d:
                domains.add(d)
    else:
        for line in text.splitlines():
            d = normalize_domain(line)
            if d:
                domains.add(d)
    return domains


def init_db(conn: sqlite3.Connection) -> None:
    # seen_domains is the historical ledger — every domain ever observed for
    # a target, with first/last-seen timestamps. It accumulates forever and
    # is NOT what diffing is based on (an all-time "ever seen" set would mean
    # anything that dropped once gets reported as dropped on every run after
    # that, forever — see latest_snapshot below for what diffing actually uses).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_domains (
            target TEXT NOT NULL,
            domain TEXT NOT NULL,
            first_seen INTEGER NOT NULL,
            last_seen INTEGER NOT NULL,
            PRIMARY KEY (target, domain)
        )
        """
    )
    # latest_snapshot holds only the domain set from the single most recent
    # run per target — fully replaced each run. Diffing compares the new
    # run's domains against this (the previous run's state), not the
    # all-time ledger, so a drop is reported exactly once, not forever.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS latest_snapshot (
            target TEXT NOT NULL,
            domain TEXT NOT NULL,
            PRIMARY KEY (target, domain)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL,
            run_time INTEGER NOT NULL,
            total_domains INTEGER NOT NULL,
            new_domains INTEGER NOT NULL,
            dropped_domains INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def get_known_domains(conn: sqlite3.Connection, target: str) -> set[str]:
    """The domain set as of the end of the previous run (not all-time
    history) — this is what the next run's diff is computed against."""
    rows = conn.execute(
        "SELECT domain FROM latest_snapshot WHERE target = ?", (target,)
    ).fetchall()
    return {r[0] for r in rows}


def diff_domains(known: set[str], current: set[str]) -> tuple[set[str], set[str]]:
    """Returns (new_domains, dropped_domains), both relative to the previous
    run's snapshot. Dropped means absent from this run but present last run —
    not necessarily gone forever (a passive source being flaky can cause a
    false drop that reappears next run)."""
    new = current - known
    dropped = known - current
    return new, dropped


def record_run(
    conn: sqlite3.Connection,
    target: str,
    current: set[str],
    new: set[str],
    dropped: set[str],
    run_time: int,
) -> None:
    # Historical ledger: upsert every domain seen this run.
    for d in current:
        conn.execute(
            """
            INSERT INTO seen_domains (target, domain, first_seen, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(target, domain) DO UPDATE SET last_seen = excluded.last_seen
            """,
            (target, d, run_time, run_time),
        )
    # Snapshot: replace entirely with this run's domain set, so the next
    # run's diff is against exactly this run, not the all-time ledger.
    conn.execute("DELETE FROM latest_snapshot WHERE target = ?", (target,))
    conn.executemany(
        "INSERT INTO latest_snapshot (target, domain) VALUES (?, ?)",
        [(target, d) for d in current],
    )
    conn.execute(
        """
        INSERT INTO runs (target, run_time, total_domains, new_domains, dropped_domains)
        VALUES (?, ?, ?, ?, ?)
        """,
        (target, run_time, len(current), len(new), len(dropped)),
    )
    conn.commit()


def format_alert_message(target: str, new: set[str], dropped: set[str], is_baseline: bool) -> str:
    if is_baseline:
        return f"[subagg monitor] {target}: baseline seeded with {len(new)} domain(s), nothing to alert on yet."
    lines = [f"[subagg monitor] {target}: {len(new)} new, {len(dropped)} dropped"]
    if new:
        lines.append("New:")
        lines.extend(f"  + {d}" for d in sorted(new))
    if dropped:
        lines.append("Dropped:")
        lines.extend(f"  - {d}" for d in sorted(dropped))
    return "\n".join(lines)


def send_slack_alert(webhook_url: str, message: str, timeout: int = 15) -> bool:
    payload = {"text": message}
    try:
        if _HAS_REQUESTS:
            resp = requests.post(webhook_url, json=payload, timeout=timeout)
            resp.raise_for_status()
            return True
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception as e:  # noqa: BLE001
        print(f"[!] Slack alert failed: {e}", file=sys.stderr)
        return False


def create_github_issue(
    repo: str, token: str, title: str, body: str, timeout: int = 15
) -> bool:
    """repo: 'owner/name'. Creates a GitHub issue via the REST API."""
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = {"title": title, "body": body}
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "subagg-monitor/1.0",
    }
    try:
        if _HAS_REQUESTS:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return True
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception as e:  # noqa: BLE001
        print(f"[!] GitHub issue creation failed: {e}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuous delta watcher / asset monitor")
    parser.add_argument("--input", required=True, help="domains.jsonl or domains.txt (e.g. from subagg.py)")
    parser.add_argument("--target", required=True, help="target label this history is tracked under, e.g. example.com")
    parser.add_argument("--db", default="monitor.db", help="SQLite history DB path (default: monitor.db)")
    parser.add_argument("--slack-webhook", default=None, help="Slack incoming webhook URL (or set SLACK_WEBHOOK_URL)")
    parser.add_argument("--github-repo", default=None, help="owner/repo to file a GitHub issue in on new deltas")
    parser.add_argument("--github-token", default=None, help="GitHub token (or set GITHUB_TOKEN); required with --github-repo")
    parser.add_argument("--quiet", action="store_true", help="suppress the printed summary (alerts still fire)")
    args = parser.parse_args()

    import os

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[!] input file not found: {input_path}", file=sys.stderr)
        return 1

    current = load_domains(input_path)
    if not current:
        print(f"[!] no valid domains parsed from {input_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    init_db(conn)

    known = get_known_domains(conn, args.target)
    is_baseline = len(known) == 0
    new, dropped = diff_domains(known, current)
    run_time = int(time.time())
    record_run(conn, args.target, current, new, dropped, run_time)
    conn.close()

    message = format_alert_message(args.target, new, dropped, is_baseline)
    if not args.quiet:
        print(message)

    if is_baseline:
        return 0

    if new or dropped:
        webhook = args.slack_webhook or os.environ.get("SLACK_WEBHOOK_URL")
        if webhook:
            if send_slack_alert(webhook, message):
                print("[+] Slack alert sent", file=sys.stderr)

        if args.github_repo:
            token = args.github_token or os.environ.get("GITHUB_TOKEN")
            if not token:
                print("[!] --github-repo given but no GitHub token (--github-token or GITHUB_TOKEN) — skipping issue", file=sys.stderr)
            else:
                title = f"[monitor] {len(new)} new asset(s) on {args.target}"
                if create_github_issue(args.github_repo, token, title, message):
                    print("[+] GitHub issue created", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
