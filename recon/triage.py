#!/usr/bin/env python3
"""
Auto-triage and dedupe utility for recon outputs.

Purpose:
  - Pull in live hosts, crawled URLs, and fuzzing output.
  - Normalize them into a single finding schema.
  - Deduplicate repeated URLs and low-value noise.
  - Rank likely-relevant targets by severity score.

Typical use:
  python recon/triage.py \
      --live recon-<target>/live.txt \
      --crawled recon-<target>/crawled.txt \
      --fuzz recon-<target>/fuzz-results.txt \
      --output recon-<target>/findings.jsonl \
      --csv recon-<target>/findings.csv

This intentionally focuses on triage and prioritization. It does not duplicate
subdomain enumeration, live host discovery, or JS extraction steps already handled
by your recon pipeline.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse, urlunparse


SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

HIGH_VALUE_KEYWORDS = {
    "admin",
    "login",
    "signin",
    "auth",
    "oauth",
    "dashboard",
    "config",
    "settings",
    "secret",
    "api",
    "graphql",
    "swagger",
    "openapi",
    "backup",
    "bak",
    "db",
    "phpmyadmin",
    "adminer",
    "git",
    "svn",
    "env",
    "debug",
    "dev",
    "test",
    "panel",
    "console",
    "manage",
    "upload",
    "download",
    "xmlrpc",
    "wp-admin",
    ".env",
    "__pycache__",
    "vendor",
    "robots.txt",
    ".git",
    "sitemap",
    "js",
    "json",
    "xml",
}

SENSITIVE_EXTENSIONS = {
    ".bak",
    ".old",
    ".orig",
    ".tmp",
    ".swp",
    ".sql",
    ".db",
    ".sqlite",
    ".log",
    ".zip",
    ".tar",
    ".gz",
    ".env",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    "openapi",
    "swagger",
    "graphql",
}


@dataclass
class Finding:
    url: str
    source: str
    status: Optional[int]
    title: Optional[str]
    score: int
    severity: str
    tags: List[str]
    details: Dict[str, Any]

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.url.lower().encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["fingerprint"] = self.fingerprint
        return data


def clean_url(raw: str) -> Optional[str]:
    if not raw:
        return None
    value = raw.strip().strip("\"'")
    # Drop trailing punctuation sometimes attached to URLs
    value = re.sub(r"[),>]+$", "", value)
    if not value:
        return None

    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
    elif value.startswith("//"):
        parsed = urlparse("https:" + value)
    else:
        # Common case: bare host in a line without scheme.
        if re.match(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value) or value.startswith("localhost"):
            parsed = urlparse(f"https://{value}")
        else:
            return None

    if not parsed.netloc:
        return None

    scheme = parsed.scheme or "https"
    host = parsed.netloc.lower()

    # Remove common user/pass noise if present
    netloc = host.split("@")[-1]
    path = parsed.path or "/"
    # Keep path but normalize trailing slash noise; keep query to preserve unique endpoints
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    if path == "":
        path = "/"

    normalized = urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
    return normalized


def normalize_tags(tags: Iterable[str]) -> List[str]:
    ordered: List[str] = []
    seen: Set[str] = set()
    for tag in tags:
        t = str(tag).strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        ordered.append(t)
    return ordered


def derive_severity(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    if score >= 20:
        return "low"
    return "info"


def extract_host(url: str) -> str:
    try:
        p = urlparse(url)
        return p.netloc.lower()
    except Exception:
        return ""


def path_looks_sensitive(url: str) -> bool:
    low = url.lower()
    return any(k in low for k in HIGH_VALUE_KEYWORDS) or any(low.endswith(ext) for ext in SENSITIVE_EXTENSIONS)


def score_finding(url: str, status: Optional[int], title: Optional[str], source: str) -> Tuple[int, List[str]]:
    score = 0
    tags: Set[str] = set()
    lower = url.lower()

    # Base scoring from status code
    if status in (200, 201, 202, 203, 204):
        score += 10
    elif status in (301, 302, 307, 308):
        score += 15
        tags.add("redirect")
    elif status in (401, 403):
        score += 20
        tags.add("auth-protected")
    elif status in (500, 502, 503):
        score += 25
        tags.add("server-error")

    # URL/endpoint heuristics
    if re.search(r"/(?:admin|login|signin|dashboard|auth|oauth|manage|console|panel)/?", lower):
        score += 35
        tags.add("admin-like")
    if re.search(r"/(?:api|graphql|swagger|openapi|docs|swagger-ui)/?", lower):
        score += 30
        tags.add("api-doc")
    if re.search(r"/(?:\.git|\.svn|\.env|\.config|config|settings|secret|backup|db|mysql|phpmyadmin|adminer)/?", lower):
        score += 45
        tags.add("sensitive-path")
    if re.search(r"(?:\.bak|\.old|\.orig|\.tmp|\.swp|\.sql|\.db|\.sqlite|\.log|\.env)$", lower):
        score += 50
        tags.add("leaked-file")

    if any(k in lower for k in HIGH_VALUE_KEYWORDS):
        score += 20
        for k in HIGH_VALUE_KEYWORDS:
            if k in lower:
                tags.add(k)

    # Titles and content hints
    if title:
        t = title.lower()
        if any(token in t for token in ["login", "admin", "dashboard", "error", "oauth", "sign in"]):
            score += 15
            tags.add("title-match")

    # Source weighting
    if source == "httpx-live":
        score += 5
    elif source == "katana-crawl":
        score += 8
    elif source == "fuzz-result":
        score += 12

    if path_looks_sensitive(url):
        score += 10
        tags.add("path-suspicious")

    # Cap score for not-a-thing URLs
    if not any(ch.isalnum() for ch in lower):
        score -= 10

    if score < 0:
        score = 0

    return score, sorted(tags)


def parse_httpx_live_line(line: str) -> Optional[Tuple[str, Optional[int], Optional[str]]]:
    s = line.strip()
    if not s:
        return None
    m = re.search(r"https?://\S+", s)
    if not m:
        return None
    url = clean_url(m.group(0))
    if not url:
        return None

    status = None
    status_match = re.search(r"\b(\d{3})\b", s)
    if status_match:
        try:
            status = int(status_match.group(1))
        except ValueError:
            status = None

    title = None
    # Usually title is after status and can include spaces, e.g. "200  ...  <title>"
    # We keep it only if there is a clean title tag format in the line.
    title_match = re.search(r"<title>(.*?)</title>", s, flags=re.I | re.S)
    if title_match:
        title = title_match.group(1).strip()
    return url, status, title


def parse_crawl_line(line: str) -> Optional[str]:
    s = line.strip()
    if not s:
        return None
    # Ignore non-URL lines or logs
    if s.startswith("["):
        return None
    m = re.search(r"https?://\S+", s)
    if not m:
        return None
    return clean_url(m.group(0))


def parse_dirfuzz_text_line(line: str) -> Optional[Tuple[str, Optional[int]]]:
    s = line.strip()
    if not s:
        return None

    # Typical line format: 200  1234  https://host/path
    m = re.search(r"\b(\d{3})\b\s+\d+\s+(https?://\S+)", s)
    if m:
        status = int(m.group(1))
        url = clean_url(m.group(2))
        if url:
            return url, status

    # Redirect line format: 301  123 https://host/path -> redirects
    m = re.search(r"\b(\d{3})\b\s+\d+\s+(https?://\S+)\s+->\s+.*", s)
    if m:
        status = int(m.group(1))
        url = clean_url(m.group(2))
        if url:
            return url, status

    # Generic URL status line from other scripts
    m = re.search(r"(https?://\S+)\s*(?:\|\s*status\s*[:=]\s*(\d{3})|\s+(\d{3}))", s, flags=re.I)
    if m:
        url = clean_url(m.group(1))
        status_text = m.group(2) or m.group(3)
        if url and status_text:
            try:
                return url, int(status_text)
            except ValueError:
                pass
    return None


def parse_jsonl_file(path: Path) -> Iterable[Tuple[str, Optional[int], Optional[str], str]]:
    """Yield (url, status, title, source)."""
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
                url = obj.get("url") or obj.get("final_url") or obj.get("target")
                if not url:
                    continue
                url = clean_url(str(url))
                if not url:
                    continue
                status = obj.get("status")
                title = obj.get("title")
                yield url, status, title, "jsonl"
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        url = item.get("url") or item.get("final_url") or item.get("target")
                        if not url:
                            continue
                        url = clean_url(str(url))
                        if not url:
                            continue
                        yield url, item.get("status"), item.get("title"), "jsonl"


def parse_ffuf_json(path: Path) -> Iterable[Tuple[str, Optional[int], Optional[str], str]]:
    """Compatibility parser for ffuf JSON output."""
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            url = obj.get("url") or obj.get("input") or obj.get("target")
            if not url:
                continue
            url = clean_url(str(url))
            if not url:
                continue
            status = obj.get("status")
            title = obj.get("title")
            yield url, status, title, "ffuf-json"


def discover_inputs(base_dir: Path) -> Dict[str, List[Path]]:
    discovered: Dict[str, List[Path]] = {"live": [], "crawled": [], "fuzz": []}
    if not base_dir.exists():
        return discovered

    for p in sorted(base_dir.iterdir()):
        if not p.is_file():
            continue
        name = p.name.lower()
        if "live" in name and p.suffix in {".txt", ".log"}:
            discovered["live"].append(p)
        elif ("crawl" in name or "urls" in name or "links" in name) and p.suffix in {".txt", ".log"}:
            discovered["crawled"].append(p)
        elif ("fuzz" in name or "result" in name or "dir" in name or name.endswith(".jsonl") or p.suffix == ".json"):
            discovered["fuzz"].append(p)
    return discovered


def init_db(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS findings (
            fingerprint TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            status INTEGER,
            source TEXT,
            score INTEGER,
            severity TEXT,
            tags TEXT,
            first_seen TEXT,
            last_seen TEXT
        )
        """
    )
    conn.commit()
    return conn


def upsert_finding(conn: sqlite3.Connection, finding: Finding):
    now = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    tags = ",".join(normalize_tags(finding.tags))
    conn.execute(
        """
        INSERT INTO findings (fingerprint, url, status, source, score, severity, tags, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(fingerprint) DO UPDATE SET
            url=excluded.url,
            status=excluded.status,
            source=excluded.source,
            score=excluded.score,
            severity=excluded.severity,
            tags=excluded.tags,
            last_seen=excluded.last_seen
        """,
        (
            finding.fingerprint,
            finding.url,
            finding.status,
            finding.source,
            finding.score,
            finding.severity,
            tags,
            now,
            now,
        ),
    )
    conn.commit()


def build_finding(url: str, source: str, status: Optional[int], title: Optional[str]) -> Finding:
    score, tags = score_finding(url, status, title, source)
    severity = derive_severity(score)
    return Finding(
        url=url,
        source=source,
        status=status,
        title=title,
        score=score,
        severity=severity,
        tags=normalize_tags(tags),
        details={"title": title, "status": status, "source": source},
    )


def collect_findings(paths: Sequence[Path], source_name: str) -> List[Finding]:
    findings: List[Finding] = []

    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() == ".jsonl":
            for url, status, title, _ in parse_jsonl_file(path):
                findings.append(build_finding(url, source_name, status, title))
            continue
        if path.suffix.lower() == ".json":
            for url, status, title, _ in parse_ffuf_json(path):
                findings.append(build_finding(url, source_name, status, title))
            continue

        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for raw in fh:
                s = raw.strip()
                if not s:
                    continue
                # httpx live line
                if source_name == "httpx-live":
                    parsed = parse_httpx_live_line(s)
                    if not parsed:
                        continue
                    url, status, title = parsed
                    findings.append(build_finding(url, source_name, status, title))
                    continue

                # katana/crawl urls or generic text URLs
                if source_name == "katana-crawl":
                    url = parse_crawl_line(s)
                    if url:
                        findings.append(build_finding(url, source_name, None, None))
                    continue

                if source_name == "fuzz-result":
                    parsed = parse_dirfuzz_text_line(s)
                    if not parsed:
                        continue
                    url, status = parsed
                    findings.append(build_finding(url, source_name, status, None))
                    continue

                # Generic fallback for plain text URL list
                if s.startswith("http://") or s.startswith("https://"):
                    url = clean_url(s)
                    if url:
                        findings.append(build_finding(url, source_name, None, None))
    return findings


def dedupe_and_sort(findings: Iterable[Finding]) -> List[Finding]:
    seen: Dict[str, Finding] = {}
    for finding in findings:
        key = finding.fingerprint
        if key not in seen:
            seen[key] = finding
            continue

        # Merge repeated entries by taking the higher of the two scores and more informative metadata.
        current = seen[key]
        current_score = max(current.score, finding.score)
        current.status = finding.status if finding.status is not None else current.status
        current.title = finding.title or current.title
        current.source = current.source if current.source == "httpx-live" else finding.source
        current.tags = normalize_tags(current.tags + finding.tags)
        current.score = current_score
        current.severity = derive_severity(current_score)
        seen[key] = current

    ordered = sorted(seen.values(), key=lambda x: (SEVERITY_ORDER.get(x.severity, -1), x.score), reverse=True)
    return ordered


def write_jsonl(path: Path, findings: Sequence[Finding]):
    with path.open("w", encoding="utf-8") as fh:
        for finding in findings:
            fh.write(json.dumps(finding.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, findings: Sequence[Finding]):
    fieldnames = ["fingerprint", "severity", "score", "status", "url", "source", "tags", "title"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for f in findings:
            writer.writerow(
                {
                    "fingerprint": f.fingerprint,
                    "severity": f.severity,
                    "score": f.score,
                    "status": f.status,
                    "url": f.url,
                    "source": f.source,
                    "tags": ", ".join(f.tags),
                    "title": f.title or "",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dedupe and prioritize recon outputs into a single findings list.")
    parser.add_argument("--live", nargs="*", default=[], help="Paths to httpx live.txt outputs")
    parser.add_argument("--crawled", nargs="*", default=[], help="Paths to katana/crawled URL files")
    parser.add_argument("--fuzz", nargs="*", default=[], help="Paths to fuzzing result files or directories")
    parser.add_argument("--dir", type=Path, default=None, help="Auto-discover results in a directory")
    parser.add_argument("--db", type=Path, default=Path("triage.db"), help="SQLite DB path for dedupe tracking")
    parser.add_argument("--output", type=Path, default=Path("findings.jsonl"), help="Output JSONL findings file")
    parser.add_argument("--csv", type=Path, default=Path("findings.csv"), help="Output CSV findings file")
    parser.add_argument("--min-score", type=int, default=0, help="Filter findings below this score")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    live_files: List[Path] = [Path(p) for p in args.live]
    crawl_files: List[Path] = [Path(p) for p in args.crawled]
    fuzz_files: List[Path] = [Path(p) for p in args.fuzz]

    if args.dir:
        discovered = discover_inputs(args.dir)
        live_files.extend(discovered["live"])
        crawl_files.extend(discovered["crawled"])
        fuzz_files.extend(discovered["fuzz"])

    if not live_files and not crawl_files and not fuzz_files and not args.dir:
        print("No inputs provided. Use --live, --crawled, --fuzz, or --dir.", file=sys.stderr)
        return 2

    findings: List[Finding] = []
    findings.extend(collect_findings(live_files, "httpx-live"))
    findings.extend(collect_findings(crawl_files, "katana-crawl"))
    findings.extend(collect_findings(fuzz_files, "fuzz-result"))

    deduped = dedupe_and_sort(findings)
    filtered = [f for f in deduped if f.score >= args.min_score]

    db_conn = init_db(args.db)
    for finding in filtered:
        upsert_finding(db_conn, finding)
    db_conn.close()

    write_jsonl(args.output, filtered)
    write_csv(args.csv, filtered)

    print(f"[*] Total raw items: {len(findings)}")
    print(f"[*] Deduped findings: {len(filtered)}")
    print(f"[*] Output JSONL: {args.output}")
    print(f"[*] Output CSV: {args.csv}")
    print(f"[*] Stored DB: {args.db}")

    if filtered:
        print("\nTop findings:")
        for f in filtered[:10]:
            print(f"- [{f.severity.upper()}:{f.score}] {f.url} | tags={', '.join(f.tags) or 'none'} | source={f.source}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
