"""Parse a Burp Suite 'Save items' XML export (Proxy > HTTP history > Save
selected items, or Save as XML). Requests are base64-encoded in <request>.
"""
from __future__ import annotations

import base64
import xml.etree.ElementTree as ET

from ..models import HttpRequest


def _decode(el, attr="base64") -> str:
    if el is None or el.text is None:
        return ""
    if el.get(attr) == "true":
        try:
            return base64.b64decode(el.text).decode("utf-8", errors="replace")
        except Exception:
            return ""
    return el.text


def _split_raw_http(raw: str) -> tuple[str, str, dict, str]:
    """Split a raw HTTP request blob into (method, path, headers, body)."""
    if "\r\n\r\n" in raw:
        head, body = raw.split("\r\n\r\n", 1)
    elif "\n\n" in raw:
        head, body = raw.split("\n\n", 1)
    else:
        head, body = raw, ""

    lines = head.replace("\r\n", "\n").split("\n")
    if not lines:
        return "GET", "/", {}, ""
    request_line = lines[0].split()
    method = request_line[0] if request_line else "GET"
    path = request_line[1] if len(request_line) > 1 else "/"

    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()

    return method, path, headers, body


def parse_xml(text: str, source: str = "") -> list[HttpRequest]:
    root = ET.fromstring(text)
    out: list[HttpRequest] = []

    for item in root.findall(".//item"):
        host_el = item.find("host")
        host = host_el.text if host_el is not None and host_el.text else ""
        port_el = item.find("port")
        port = port_el.text if port_el is not None else None
        proto_el = item.find("protocol")
        proto = (proto_el.text if proto_el is not None else None) or "https"

        request_el = item.find("request")
        raw_req = _decode(request_el)
        if not raw_req:
            # Fall back to <url> + minimal GET if <request> wasn't present/decodable.
            url_el = item.find("url")
            url = url_el.text if url_el is not None and url_el.text else None
            if not url:
                continue
            out.append(HttpRequest(method="GET", url=url, headers={}, body=None, source=source))
            continue

        method, path, headers, body = _split_raw_http(raw_req)

        host_header = headers.get("Host") or host
        default_port = "443" if proto == "https" else "80"
        port_part = "" if not port or port == default_port else f":{port}"
        url = f"{proto}://{host_header}{port_part}{path}"

        out.append(HttpRequest(
            method=method,
            url=url,
            headers=headers,
            body=body if body else None,
            source=source,
        ))

    return out
