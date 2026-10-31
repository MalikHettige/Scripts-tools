"""Input parsers: turn a Burp/ZAP export or a raw request file into a list of
HttpRequest objects. Dispatch is by file sniffing, not extension, since Burp
and ZAP both export .xml.
"""
from __future__ import annotations

from pathlib import Path

from ..models import HttpRequest
from . import burp, zap, raw


def parse_any(path: str) -> list[HttpRequest]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    stripped = text.lstrip()

    if stripped.startswith("<?xml") or stripped.startswith("<items") or stripped.startswith("<OWASPZAPReport"):
        if "<item>" in text and "<request" in text and "burpVersion" not in text and "<alerts" not in text:
            # Ambiguous generic XML - try Burp first, ZAP second.
            pass
        if "<alerts" in text or "OWASPZAPReport" in text or "<messages" in text:
            return zap.parse_xml(text, source=path)
        return burp.parse_xml(text, source=path)

    if stripped.startswith("{") or stripped.startswith("["):
        # Could be ZAP JSON export or a raw JSON request list.
        if '"messages"' in text or '"site"' in text and '"alerts"' in text:
            return zap.parse_json(text, source=path)
        parsed = raw.try_parse_json_requests(text, source=path)
        if parsed:
            return parsed
        return zap.parse_json(text, source=path)

    # Fall back to raw request text (one-per-line "METHOD URL" or
    # ---- separated raw HTTP request blocks).
    return raw.parse_text(text, source=path)
