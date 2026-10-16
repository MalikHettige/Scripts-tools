#!/usr/bin/env python3
"""
Auto-draft report generator for recon findings.

The script reads a triage output file (findings.jsonl from recon/triage.py) and
creates a Markdown report draft for a specific finding or for all findings.

Example:
  python recon/reportgen.py --input recon-target/findings.jsonl --id <fingerprint>
  python recon/reportgen.py --input recon-target/findings.jsonl --top 5 --output recon-target/report.md

The default output is a human-editable report in Markdown. It is meant to save
repetitive writing time while still leaving a reviewer in control of the final
version.
"""

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from jinja2 import Template

DEFAULT_TEMPLATE = Path(__file__).with_name("report_template.j2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Markdown draft reports from recon findings.")
    parser.add_argument("--input", required=True, help="Path to findings.jsonl or a single JSON finding file")
    parser.add_argument("--id", help="Fingerprint, index, or URL to select a specific finding")
    parser.add_argument("--top", type=int, help="Generate a summary report for the top N findings")
    parser.add_argument("--output", type=Path, default=Path("report.md"), help="Output Markdown file")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Jinja2 Markdown template path")
    parser.add_argument("--stdout", action="store_true", help="Print generated Markdown to stdout in addition to writing the file")
    parser.add_argument("--title-prefix", default="[Finding]", help="Text prefix in generated title")
    return parser.parse_args()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                findings.append(obj)
    return findings


def select_finding(findings: List[Dict[str, Any]], selector: Optional[str]) -> Optional[Dict[str, Any]]:
    if selector is None:
        return None

    selector = selector.strip()
    if not selector:
        return None

    # If the user passed a numeric index, use that
    if selector.isdigit():
        idx = int(selector)
        if 0 <= idx < len(findings):
            return findings[idx]
        return None

    # Match against fingerprint or URL
    for item in findings:
        if selector == str(item.get("fingerprint")):
            return item
        if selector == str(item.get("url")):
            return item
    return None


def safe_score(value: Any) -> int:
    """Coerce a finding's score to int for sorting/ranking, tolerating
    missing or malformed values (e.g. a hand-edited or third-party-produced
    findings file) instead of crashing the whole run."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def host_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


def build_context(finding: Dict[str, Any], title_prefix: str) -> Dict[str, Any]:
    url = str(finding.get("url") or "Unknown URL")
    status = finding.get("status")
    severity = str(finding.get("severity") or "info").upper()
    score = finding.get("score", 0)
    tags = finding.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    details_raw = finding.get("details")
    details_safe: Dict[str, Any] = details_raw if isinstance(details_raw, dict) else {}
    title = finding.get("title") or details_safe.get("title")
    if not title:
        title = f"{severity} issue: {host_from_url(url)}"

    # Build default summary
    summary = (
        f"A {severity.lower()} finding was identified at {url}. "
        f"The endpoint returned status {status if status is not None else 'unknown'} with a risk score of {score}."
    )

    # Create a generic impact section
    impact = (
        "This endpoint could expose application logic, sensitive metadata, or operational details to an attacker, "
        "depending on the surrounding application behavior and authentication boundary."
    )

    # Remediation defaults
    remediation = [
        "Restrict access to the endpoint with proper authentication and authorization checks.",
        "Remove or lock down sensitive files, backups, or admin-like paths from public access.",
        "Review server configuration and application routing for unintended exposure.",
        "Validate with a second check after remediation to confirm the issue is no longer reachable.",
    ]

    # shlex.quote (not an f-string with a bare '{url}') because `url` is
    # attacker-influenced (scraped/crawled/fuzzed from the target) and this
    # command is meant to be copy-pasted straight into a shell by the analyst.
    # An unescaped single quote in the URL would otherwise break out of the
    # quoting and let arbitrary shell commands run when the line is pasted.
    quoted_url = shlex.quote(url)
    curl_cmd = f"curl -sS -D - -o /dev/null {quoted_url}"
    if status is not None:
        # Literal %{http_code} is curl's own -w syntax, not a Python format
        # field, so it must not sit inside an f-string (the original code
        # had `f"...%{http_code}\n..."`, which Python tried to evaluate as
        # a variable named http_code and raised NameError on every finding
        # that had a status).
        curl_cmd = "curl -sS -D - -o /dev/null -w 'HTTP %{http_code}\\n' " + quoted_url

    evidence = [
        {"label": "URL", "value": url},
        {"label": "Severity", "value": severity},
        {"label": "Risk score", "value": str(score)},
        {"label": "HTTP status", "value": str(status) if status is not None else "unknown"},
        {"label": "Tags", "value": ", ".join(tags) if tags else "none"},
    ]

    # include additional evidence from details if present
    details = finding.get("details") or {}
    if isinstance(details, dict):
        for key, value in details.items():
            if key in {"title", "status", "source"}:
                continue
            if value is not None and value not in ("", []):
                evidence.append({"label": str(key).replace("_", " ").title(), "value": str(value)})

    context = {
        "title_prefix": title_prefix,
        "title": title,
        "summary": summary,
        "impact": impact,
        "severity": severity,
        "score": score,
        "host": host_from_url(url),
        "url": url,
        "status": status if status is not None else "unknown",
        "evidence": evidence,
        "curl_cmd": curl_cmd,
        "tags": tags,
        "remediation": remediation,
        "source": finding.get("source") or "unknown",
    }
    return context


def render_report(context: Dict[str, Any], template: Path) -> str:
    template_path = template if template.exists() else DEFAULT_TEMPLATE
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    template_text = template_path.read_text(encoding="utf-8")
    return Template(template_text).render(**context)


def format_top_report(findings: List[Dict[str, Any]], title_prefix: str) -> str:
    if not findings:
        return "No findings were available to include in the report.\n"
    selected = findings[:10]
    context = {
        "title_prefix": title_prefix,
        "title": "Recon findings summary",
        "summary": f"This report summarizes the top {len(selected)} findings from the latest recon triage run.",
        "impact": "These findings should be reviewed and triaged manually before any deeper exploitation work.",
        "severity": "SUMMARY",
        "score": 0,
        "host": "Multiple hosts",
        "url": "N/A",
        "status": "n/a",
        "evidence": [
            {"label": "Total findings", "value": str(len(findings))},
            {"label": "Report items", "value": str(len(selected))},
        ],
        "curl_cmd": "N/A",
        "tags": ["summary"],
        "remediation": [
            "Review the top findings in priority order.",
            "Validate any sensitive or admin-like findings before doing broader testing.",
            "Ensure disclosures or route restrictions are applied before moving to exploit validation.",
        ],
        "source": "triage-summary",
        "top_findings": [
            {
                "url": f.get("url"),
                "severity": f.get("severity"),
                "score": f.get("score"),
                "status": f.get("status"),
                "tags": f.get("tags", []),
            }
            for f in selected
        ],
    }
    template_text = DEFAULT_TEMPLATE.read_text(encoding="utf-8")
    return Template(template_text).render(**context)


def main() -> int:
    args = parse_args()

    try:
        findings = load_jsonl(Path(args.input))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not findings:
        print("No valid findings were found in the input file.", file=sys.stderr)
        return 1

    selected: Optional[Dict[str, Any]]
    if args.top is not None:
        selected = None
        report_text = format_top_report(findings[:args.top], args.title_prefix)
    else:
        selected = select_finding(findings, args.id)
        if selected is None:
            if args.id:
                print(f"No matching finding found for selector: {args.id}", file=sys.stderr)
                return 1
            # Default to the highest-ranked item if no selector is passed
            selected = max(findings, key=lambda x: safe_score(x.get("score", 0)))
        report_text = render_report(build_context(selected, args.title_prefix), args.template)

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")

    if args.stdout:
        print(report_text)

    print(f"[*] Wrote report to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


