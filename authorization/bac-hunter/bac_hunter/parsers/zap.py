"""Parse OWASP ZAP exports. Two shapes are supported:

1. ZAP's standard XML/JSON alert report (Report > Generate Report, or the
   core API's alerts view), where each <alertitem>/alert object carries
   requestheader + requestbody as raw text.
2. The "Export Messages" / HAR-ish JSON some ZAP setups produce, with a
   top-level list of messages each holding requestHeader/requestBody.

Both are sniffed loosely; if your ZAP export doesn't match either shape,
export as HAR instead and convert with any har-to-raw tool, or save requests
as raw text (one block per request) and use --format raw.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from ..models import HttpRequest


def _split_raw_http(raw: str) -> tuple[str, str, dict]:
    raw = raw.replace("\r\n", "\n")
    lines = raw.split("\n")
    if not lines:
        return "GET", "/", {}
    request_line = lines[0].split()
    method = request_line[0] if request_line else "GET"
    path = request_line[1] if len(request_line) > 1 else "/"
    headers = {}
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
    return method, path, headers


def _build_url(headers: dict, path: str) -> str:
    host = headers.get("Host", "")
    scheme = "https"
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{scheme}://{host}{path}"


def parse_xml(text: str, source: str = "") -> list[HttpRequest]:
    root = ET.fromstring(text)
    out: list[HttpRequest] = []
    for alert in root.findall(".//alertitem") + root.findall(".//instance"):
        rh = alert.find("requestheader")
        rb = alert.find("requestbody")
        if rh is None or not rh.text:
            continue
        method, path, headers = _split_raw_http(rh.text)
        url = _build_url(headers, path)
        body = rb.text if rb is not None and rb.text else None
        out.append(HttpRequest(method=method, url=url, headers=headers, body=body, source=source))
    return out


def parse_json(text: str, source: str = "") -> list[HttpRequest]:
    data = json.loads(text)
    out: list[HttpRequest] = []

    def handle_message(msg: dict):
        rh = msg.get("requestHeader") or msg.get("requestheader")
        rb = msg.get("requestBody") or msg.get("requestbody")
        if not rh:
            return
        method, path, headers = _split_raw_http(rh)
        url = _build_url(headers, path)
        out.append(HttpRequest(method=method, url=url, headers=headers, body=rb or None, source=source))

    def walk(node):
        if isinstance(node, dict):
            if "requestHeader" in node or "requestheader" in node:
                handle_message(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return out
