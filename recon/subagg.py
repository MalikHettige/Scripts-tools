#!/usr/bin/env python3
"""
subagg.py — passive subdomain aggregator

Queries crt.sh (certificate transparency), and optionally VirusTotal/OTX and
local amass/subfinder binaries, merges + dedupes everything into one
canonical domain list, scoped to the target apex domain.

Usage:
    python subagg.py example.com
    python subagg.py example.com -o out/ --amass --subfinder
    VT_API_KEY=xxx OTX_API_KEY=yyy python subagg.py example.com --vt --otx

Output:
    <outdir>/domains.txt    - one hostname per line, sorted
    <outdir>/domains.jsonl  - {"domain": "...", "sources": ["crtsh", ...]}

No required third-party deps for the core (crt.sh) path — uses urllib from
the standard library so it runs with zero setup. `requests` is used if
present (nicer timeouts/retries) but isn't required.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import requests  # optional, nicer than urllib if available
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$"
)


def _http_get(url: str, timeout: int = 20, headers: dict | None = None) -> str | None:
    """GET a URL and return the response body as text, or None on failure."""
    headers = headers or {"User-Agent": "subagg/1.0"}
    try:
        if _HAS_REQUESTS:
            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            return resp.text
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001 - we want to degrade gracefully, not crash
        print(f"[!] request failed for {url}: {e}", file=sys.stderr)
        return None


def normalize_domain(raw: str) -> str | None:
    """Lowercase, strip wildcard/trailing dot/whitespace, validate shape."""
    if not raw:
        return None
    d = raw.strip().lower().rstrip(".")
    if d.startswith("*."):
        d = d[2:]
    # crt.sh sometimes returns multiple names separated by newlines in one field
    if not d or " " in d:
        return None
    if not HOSTNAME_RE.match(d):
        return None
    return d


def in_scope(domain: str, apex: str) -> bool:
    apex = apex.lower().rstrip(".")
    return domain == apex or domain.endswith("." + apex)


def parse_crtsh_json(data: str, apex: str) -> set[str]:
    """Parse crt.sh's JSON output into a set of in-scope, normalized hostnames."""
    found: set[str] = set()
    try:
        rows = json.loads(data)
    except json.JSONDecodeError:
        return found
    for row in rows:
        name_value = row.get("name_value", "") if isinstance(row, dict) else ""
        for line in name_value.split("\n"):
            d = normalize_domain(line)
            if d and in_scope(d, apex):
                found.add(d)
    return found


def query_crtsh(apex: str, timeout: int = 20) -> set[str]:
    url = f"https://crt.sh/?q=%25.{apex}&output=json"
    body = _http_get(url, timeout=timeout)
    if body is None:
        print("[!] crt.sh query failed (network/parse) — skipping this source", file=sys.stderr)
        return set()
    found = parse_crtsh_json(body, apex)
    print(f"[+] crt.sh: {len(found)} hostnames", file=sys.stderr)
    return found


def parse_vt_json(data: str, apex: str) -> set[str]:
    found: set[str] = set()
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return found
    for item in parsed.get("data", []):
        d = normalize_domain(item.get("id", "")) if isinstance(item, dict) else None
        if d and in_scope(d, apex):
            found.add(d)
    return found


def query_vt(apex: str, api_key: str, timeout: int = 20) -> set[str]:
    url = f"https://www.virustotal.com/api/v3/domains/{apex}/subdomains?limit=40"
    headers = {"x-apikey": api_key, "User-Agent": "subagg/1.0"}
    body = _http_get(url, timeout=timeout, headers=headers)
    if body is None:
        print("[!] VirusTotal query failed — skipping this source", file=sys.stderr)
        return set()
    found = parse_vt_json(body, apex)
    print(f"[+] VirusTotal: {len(found)} hostnames", file=sys.stderr)
    return found


def parse_otx_json(data: str, apex: str) -> set[str]:
    found: set[str] = set()
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return found
    for item in parsed.get("passive_dns", []):
        hostname = item.get("hostname", "") if isinstance(item, dict) else ""
        d = normalize_domain(hostname)
        if d and in_scope(d, apex):
            found.add(d)
    return found


def query_otx(apex: str, api_key: str, timeout: int = 20) -> set[str]:
    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{apex}/passive_dns"
    headers = {"X-OTX-API-KEY": api_key, "User-Agent": "subagg/1.0"}
    body = _http_get(url, timeout=timeout, headers=headers)
    if body is None:
        print("[!] OTX query failed — skipping this source", file=sys.stderr)
        return set()
    found = parse_otx_json(body, apex)
    print(f"[+] OTX: {len(found)} hostnames", file=sys.stderr)
    return found


def parse_tool_output(text: str, apex: str) -> set[str]:
    """Parse line-based subdomain output (amass/subfinder both emit one host per line)."""
    found: set[str] = set()
    for line in text.splitlines():
        d = normalize_domain(line)
        if d and in_scope(d, apex):
            found.add(d)
    return found


def run_local_tool(binary: str, args: list[str], timeout: int = 300) -> str | None:
    path = shutil.which(binary)
    if not path:
        print(f"[!] {binary} not found on PATH — skipping", file=sys.stderr)
        return None
    try:
        result = subprocess.run(
            [path, *args], capture_output=True, text=True, timeout=timeout, check=False
        )
        if result.returncode != 0:
            print(f"[!] {binary} exited {result.returncode}: {result.stderr.strip()[:300]}", file=sys.stderr)
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"[!] {binary} timed out after {timeout}s", file=sys.stderr)
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[!] {binary} failed to run: {e}", file=sys.stderr)
        return None


def run_amass(apex: str, timeout: int = 300) -> set[str]:
    out = run_local_tool("amass", ["enum", "-passive", "-d", apex], timeout=timeout)
    if out is None:
        return set()
    found = parse_tool_output(out, apex)
    print(f"[+] amass: {len(found)} hostnames", file=sys.stderr)
    return found


def run_subfinder(apex: str, timeout: int = 300) -> set[str]:
    out = run_local_tool("subfinder", ["-d", apex, "-silent"], timeout=timeout)
    if out is None:
        return set()
    found = parse_tool_output(out, apex)
    print(f"[+] subfinder: {len(found)} hostnames", file=sys.stderr)
    return found


def merge_sources(results: dict[str, set[str]]) -> dict[str, list[str]]:
    """results: {source_name: set_of_domains} -> {domain: [sources...]} sorted."""
    merged: dict[str, set[str]] = {}
    for source, domains in results.items():
        for d in domains:
            merged.setdefault(d, set()).add(source)
    return {d: sorted(srcs) for d, srcs in sorted(merged.items())}


def write_outputs(merged: dict[str, list[str]], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    txt_path = outdir / "domains.txt"
    jsonl_path = outdir / "domains.jsonl"
    with txt_path.open("w") as f:
        for d in merged:
            f.write(d + "\n")
    with jsonl_path.open("w") as f:
        for d, sources in merged.items():
            f.write(json.dumps({"domain": d, "sources": sources}) + "\n")
    print(f"[+] wrote {len(merged)} unique domains -> {txt_path}, {jsonl_path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Passive subdomain aggregator")
    parser.add_argument("domain", help="apex domain to enumerate, e.g. example.com")
    parser.add_argument("-o", "--output-dir", default=".", help="output directory (default: current dir)")
    parser.add_argument("--timeout", type=int, default=20, help="per-request timeout in seconds (default: 20)")
    parser.add_argument("--no-crtsh", action="store_true", help="skip crt.sh (on by default)")
    parser.add_argument("--vt", action="store_true", help="also query VirusTotal (needs VT_API_KEY env var)")
    parser.add_argument("--otx", action="store_true", help="also query OTX (needs OTX_API_KEY env var)")
    parser.add_argument("--amass", action="store_true", help="also run local amass (passive mode) if installed")
    parser.add_argument("--subfinder", action="store_true", help="also run local subfinder if installed")
    args = parser.parse_args()

    apex = args.domain.strip().lower().rstrip(".")
    if not normalize_domain(apex):
        print(f"[!] '{args.domain}' doesn't look like a valid domain", file=sys.stderr)
        return 1

    results: dict[str, set[str]] = {}

    if not args.no_crtsh:
        results["crtsh"] = query_crtsh(apex, timeout=args.timeout)

    if args.vt:
        import os
        key = os.environ.get("VT_API_KEY")
        if not key:
            print("[!] --vt given but VT_API_KEY not set — skipping", file=sys.stderr)
        else:
            results["virustotal"] = query_vt(apex, key, timeout=args.timeout)

    if args.otx:
        import os
        key = os.environ.get("OTX_API_KEY")
        if not key:
            print("[!] --otx given but OTX_API_KEY not set — skipping", file=sys.stderr)
        else:
            results["otx"] = query_otx(apex, key, timeout=args.timeout)

    if args.amass:
        results["amass"] = run_amass(apex)

    if args.subfinder:
        results["subfinder"] = run_subfinder(apex)

    if not any(results.values()):
        print("[!] no results from any source — nothing to write", file=sys.stderr)
        return 1

    merged = merge_sources(results)
    write_outputs(merged, Path(args.output_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
