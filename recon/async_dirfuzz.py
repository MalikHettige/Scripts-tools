#!/usr/bin/env python3
"""
Async directory/file fuzzer.

Usage:
  python async_dirfuzz.py TARGET wordlist.txt
  python async_dirfuzz.py TARGET wordlist.txt --ext json,bak,old,swp
  python async_dirfuzz.py TARGET wordlist.txt -o results.txt -c 30 -t 8

Key behavior:
  - Calibrates against soft-404s (apps that return 200 with a "not found" page)
    before the real run, so those don't flood your output as false positives.
  - Writes matches to a results file AND prints them live.
  - Flags redirects separately from real hits.
"""
import argparse
import asyncio
import sys
from pathlib import Path

import aiohttp
from aiohttp import ClientTimeout
from aiohttp.resolver import ThreadedResolver
from asyncio import Semaphore

HEADERS = {"User-Agent": "dirfuzz/2.0 (+you@example.com)"}


async def fetch(session, url):
    """Single GET, returns (status, length, final_url) or raises."""
    async with session.get(url, allow_redirects=False) as resp:
        text = await resp.text(errors="ignore")
        return resp.status, len(text), str(resp.url)


async def calibrate(session, target, scheme):
    """
    Probe a few deliberately-garbage paths to learn what a 'not found'
    response actually looks like on this target (status + length).
    Returns a set of (status, length) signatures to treat as noise.
    """
    junk_paths = ["asjdkqwoeiuzxcv123", "zzz9999notarealpath", "qpwoeiruty000000"]
    signatures = set()
    for junk in junk_paths:
        url = f"{scheme}://{target}/{junk}"
        try:
            status, length, _ = await fetch(session, url)
            signatures.add((status, length))
        except Exception:
            pass
    return signatures


async def probe(session, sem, url, baseline, results, out_fh):
    async with sem:
        try:
            status, length, final_url = await fetch(session, url)
        except Exception as e:
            # Some exceptions (notably asyncio.TimeoutError) stringify to an
            # empty string, which looks like a silent/blank failure. Fall
            # back to the exception's type name so there's always something
            # readable here.
            msg = str(e) or type(e).__name__
            print(f"ERR    ----   {url}  -> {msg}")
            return

        if status in (404, 410):
            return
        if (status, length) in baseline:
            return  # matches a known soft-404 signature, skip

        if status in (301, 302, 307, 308):
            line = f"{status} {length:6d} {url}  -> redirects"
        else:
            line = f"{status} {length:6d} {url}"

        print(line)
        results.append(line)
        if out_fh:
            out_fh.write(line + "\n")
            out_fh.flush()


async def main(args):
    sem = Semaphore(args.concurrency)
    timeout = ClientTimeout(total=args.timeout)
    extensions = [e.strip() for e in args.ext.split(",") if e.strip()] if args.ext else [""]

    results = []
    out_fh = open(args.output, "w") if args.output else None

    # Use the threaded resolver (plain system getaddrinfo) instead of aiohttp's
    # default aiodns-based resolver. aiodns does raw UDP DNS queries directly,
    # which can get silently blocked/filtered by VPN clients (observed with
    # Proton VPN on Windows) even when normal system DNS (nslookup, browsers,
    # curl) resolves fine. This avoids that failure mode entirely.
    connector = aiohttp.TCPConnector(resolver=ThreadedResolver())
    async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS, connector=connector) as session:
        print("[*] Calibrating against soft-404 responses...")
        baseline = await calibrate(session, args.target, args.scheme)
        if baseline:
            print(f"[*] Learned {len(baseline)} soft-404 signature(s), will be filtered.")

        words = [w.strip() for w in Path(args.wordlist).read_text().splitlines() if w.strip()]
        tasks = []
        for word in words:
            for ext in extensions:
                path = f"{word}.{ext}" if ext else word
                url = f"{args.scheme}://{args.target}/{path}"
                tasks.append(asyncio.create_task(probe(session, sem, url, baseline, results, out_fh)))

        await asyncio.gather(*tasks)

    if out_fh:
        out_fh.close()
        print(f"[*] {len(results)} result(s) written to {args.output}")


def parse_args():
    p = argparse.ArgumentParser(description="Async directory/file fuzzer with soft-404 filtering.")
    p.add_argument("target", help="Target host, no scheme, e.g. example.com")
    p.add_argument("wordlist", help="Path to wordlist file")
    p.add_argument("-o", "--output", help="Write results to this file as well as stdout")
    p.add_argument("-c", "--concurrency", type=int, default=20, help="Concurrent requests (default 20)")
    p.add_argument("-t", "--timeout", type=int, default=10, help="Per-request timeout in seconds (default 10)")
    p.add_argument("--ext", help="Comma-separated extensions to append per word, e.g. json,bak,old")
    p.add_argument("--scheme", choices=["https", "http"], default="https",
                    help="Scheme to use (default https). Use --scheme http for targets with no TLS on 443 "
                         "(you'll see blank/TimeoutError ERR lines on every request if you get this wrong).")
    return p.parse_args()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python async_dirfuzz.py TARGET wordlist.txt [--ext json,bak] [-o results.txt] [-c N] [-t N]")
        sys.exit(2)
    asyncio.run(main(parse_args()))
