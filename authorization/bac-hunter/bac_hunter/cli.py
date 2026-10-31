from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .parsers import parse_any
from .sessions import load_sessions
from .mutations import STRATEGIES
from .engine import run
from .report import to_markdown, to_json


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bac-hunter",
        description=(
            "Automated broken-access-control testing: replays captured requests "
            "under multiple session identities and with swapped object IDs, flags "
            "anomalies for manual verification. For use only against targets you "
            "are authorized to test."
        ),
    )
    p.add_argument("--input", required=True, help="Burp/ZAP export file or raw request file")
    p.add_argument("--sessions", required=True, help="JSON or YAML file with >=2 session configs")
    p.add_argument(
        "--strategies", nargs="+", default=list(STRATEGIES),
        choices=list(STRATEGIES),
        help=f"which mutation strategies to run (default: all of {list(STRATEGIES)})",
    )
    p.add_argument("--out", default="bac-report.md", help="output report path")
    p.add_argument("--format", choices=["markdown", "json"], default=None,
                    help="report format (default: inferred from --out extension, else markdown)")
    p.add_argument("--concurrency", type=int, default=10, help="max concurrent requests (default 10)")
    p.add_argument("--timeout", type=float, default=15.0, help="per-request timeout in seconds")
    p.add_argument("--delay", type=float, default=0.0, help="seconds to sleep after each request (politeness/rate-limit)")
    p.add_argument("--max-requests", type=int, default=None, help="cap the number of candidate params tested (for a quick pass)")
    p.add_argument("--insecure", action="store_true", help="disable TLS certificate verification")
    p.add_argument("--target-label", default="", help="label for the report header, e.g. program name")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    print(f"[*] Parsing input: {args.input}")
    try:
        requests = parse_any(args.input)
    except Exception as e:
        print(f"[!] Failed to parse --input: {e}", file=sys.stderr)
        sys.exit(1)
    if not requests:
        print("[!] No requests extracted from --input. Check the file format "
              "(Burp XML export, ZAP export, or raw request text).", file=sys.stderr)
        sys.exit(1)
    print(f"[*] Loaded {len(requests)} requests")

    print(f"[*] Loading sessions: {args.sessions}")
    try:
        sessions = load_sessions(args.sessions)
    except Exception as e:
        print(f"[!] Failed to load --sessions: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"[*] Loaded {len(sessions)} sessions: " + ", ".join(f"{s.name}(level={s.level})" for s in sessions))

    print(f"[*] Strategies: {args.strategies}")

    done = {"n": 0}

    def progress():
        done["n"] += 1
        if done["n"] % 25 == 0:
            print(f"[*] ...{done['n']} candidates tested")

    findings, candidates_tested = asyncio.run(run(
        requests=requests,
        sessions=sessions,
        strategy_names=args.strategies,
        concurrency=args.concurrency,
        timeout=args.timeout,
        verify_ssl=not args.insecure,
        delay=args.delay,
        max_requests=args.max_requests,
        progress_cb=progress,
    ))

    print(f"[*] Tested {candidates_tested} candidate params, {len(findings)} findings flagged")

    fmt = args.format
    if fmt is None:
        fmt = "json" if args.out.endswith(".json") else "markdown"

    text = to_json(findings, candidates_tested, args.target_label) if fmt == "json" \
        else to_markdown(findings, candidates_tested, args.target_label)

    Path(args.out).write_text(text)
    print(f"[*] Report written to {args.out}")

    high = sum(1 for f in findings if f.confidence == "high")
    if high:
        print(f"[!] {high} HIGH confidence finding(s) - verify manually before writing up.")


if __name__ == "__main__":
    main()
