"""Rebuild an HttpRequest with one candidate param's value swapped, without
disturbing anything else about the request (other query params, body
structure, headers).
"""
from __future__ import annotations

import json
from urllib.parse import urlsplit, urlunsplit, urlencode, parse_qsl

from .models import HttpRequest, ParamLocation


def with_param_value(req: HttpRequest, loc: ParamLocation, new_value: str) -> HttpRequest:
    clone = req.clone()

    if loc.kind == "query":
        parts = urlsplit(req.url)
        pairs = parse_qsl(parts.query, keep_blank_values=True)
        pairs = [(k, new_value if k == loc.name and v == loc.value else v) for k, v in pairs]
        new_query = urlencode(pairs)
        clone.url = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    elif loc.kind == "path":
        parts = urlsplit(req.url)
        segments = parts.path.split("/")
        for i, seg in enumerate(segments):
            if seg == loc.value:
                segments[i] = new_value
                break
        new_path = "/".join(segments)
        clone.url = urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))

    elif loc.kind == "header":
        clone.headers = dict(req.headers)
        clone.headers[loc.name] = new_value

    elif loc.kind in ("json_body", "form_body") and req.body:
        if loc.kind == "json_body":
            try:
                data = json.loads(req.body)
            except Exception:
                return clone
            _set_json_path(data, loc.json_path, new_value)
            clone.body = json.dumps(data)
        else:
            pairs = parse_qsl(req.body, keep_blank_values=True)
            pairs = [(k, new_value if k == loc.name and v == loc.value else v) for k, v in pairs]
            clone.body = urlencode(pairs)

    return clone


def _set_json_path(obj, dotted_path: str, value: str):
    """Walk a dotted path like 'data.owner.id' or 'items[0].id' and set it."""
    tokens = []
    for part in dotted_path.replace("]", "").split("."):
        if "[" in part:
            name, idx = part.split("[")
            if name:
                tokens.append(name)
            tokens.append(int(idx))
        else:
            tokens.append(part)

    cur = obj
    for t in tokens[:-1]:
        cur = cur[t]
    last = tokens[-1]
    # Preserve original type (int vs str) where possible.
    if isinstance(cur[last], int) and value.lstrip("-").isdigit():
        cur[last] = int(value)
    else:
        cur[last] = value
