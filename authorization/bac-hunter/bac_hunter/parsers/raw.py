"""Parse plain-text request input. Two accepted shapes:

1. One request per line: "METHOD URL" (optionally "METHOD URL  Header: v; Header2: v2")
2. Raw HTTP request blocks, each separated by a line of 3+ dashes ("---"),
   e.g. what you'd paste out of Burp's "Copy as request" or curl -v captures.

A JSON list of {"method","url","headers","body"} objects is also accepted
via try_parse_json_requests, used as a fallback when a .json file isn't a
ZAP export.
"""
from __future__ import annotations

import json
import re

from ..models import HttpRequest

LINE_RE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(\S+)(?:\s+(.*))?$", re.IGNORECASE)


def try_parse_json_requests(text: str, source: str = "") -> list[HttpRequest]:
    try:
        data = json.loads(text)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for obj in data:
        if not isinstance(obj, dict) or "url" not in obj:
            return []  # not our shape; let caller try something else
        out.append(HttpRequest(
            method=obj.get("method", "GET").upper(),
            url=obj["url"],
            headers=obj.get("headers", {}) or {},
            body=obj.get("body"),
            source=source,
        ))
    return out


def _parse_raw_block(block: str, source: str) -> HttpRequest | None:
    block = block.strip("\n")
    if not block.strip():
        return None
    raw = block.replace("\r\n", "\n")
    lines = raw.split("\n")
    request_line = lines[0].split()
    if len(request_line) < 2:
        return None
    method, path = request_line[0].upper(), request_line[1]

    headers = {}
    body_lines = []
    in_body = False
    for line in lines[1:]:
        if in_body:
            body_lines.append(line)
            continue
        if line.strip() == "":
            in_body = True
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()

    body = "\n".join(body_lines) if body_lines else None
    host = headers.get("Host", "")
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    else:
        url = f"https://{host}{path}" if host else path

    return HttpRequest(method=method, url=url, headers=headers, body=body, source=source)


def parse_text(text: str, source: str = "") -> list[HttpRequest]:
    out: list[HttpRequest] = []

    if re.search(r"^-{3,}\s*$", text, re.MULTILINE):
        blocks = re.split(r"^-{3,}\s*$", text, flags=re.MULTILINE)
        for block in blocks:
            req = _parse_raw_block(block, source)
            if req:
                out.append(req)
        if out:
            return out

    # One-line-per-request form.
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        method, url, header_str = m.group(1).upper(), m.group(2), m.group(3)
        headers = {}
        if header_str:
            for part in header_str.split(";"):
                part = part.strip()
                if ":" in part:
                    k, v = part.split(":", 1)
                    headers[k.strip()] = v.strip()
        out.append(HttpRequest(method=method, url=url, headers=headers, body=None, source=source))

    return out
