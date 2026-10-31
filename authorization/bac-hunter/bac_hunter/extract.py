"""Find candidate identifier parameters (user_id, order_id, uuid-shaped
values, etc.) inside a request: query string, path segments, JSON body,
form body, and a small set of identifier-bearing headers.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit, parse_qsl

from .models import HttpRequest, CandidateParam, ParamLocation, looks_like_id_param, looks_like_id_value

ID_HEADER_NAMES = {"x-user-id", "x-account-id", "x-org-id", "x-tenant-id"}

# A bare path segment that's a UUID/numeric/Mongo-OID, with no param name
# attached (e.g. /orders/482913/items) - we synthesize a name from the
# preceding path segment ("orders" -> "orders_id").
PATH_SEGMENT_RE = re.compile(r"[^/]+")


def _json_leaves(obj, prefix=""):
    """Yield (dotted_path, key, value) for every scalar leaf in a JSON structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                yield from _json_leaves(v, path)
            else:
                yield path, k, v
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            path = f"{prefix}[{i}]"
            if isinstance(v, (dict, list)):
                yield from _json_leaves(v, path)
            else:
                yield path, f"[{i}]", v


def extract_candidates(req: HttpRequest) -> list[CandidateParam]:
    out: list[CandidateParam] = []

    # --- query params ---
    parts = urlsplit(req.url)
    for name, value in parse_qsl(parts.query, keep_blank_values=True):
        if looks_like_id_param(name) or looks_like_id_value(value):
            out.append(CandidateParam(req, ParamLocation("query", name, value)))

    # --- path segments ---
    segments = [s for s in parts.path.split("/") if s]
    for i, seg in enumerate(segments):
        if looks_like_id_value(seg):
            prev = segments[i - 1] if i > 0 else "path"
            synthetic_name = f"{prev.rstrip('s')}_id"
            out.append(CandidateParam(req, ParamLocation("path", synthetic_name, seg)))

    # --- headers ---
    for k, v in (req.headers or {}).items():
        if k.lower() in ID_HEADER_NAMES:
            out.append(CandidateParam(req, ParamLocation("header", k, v)))

    # --- body ---
    if req.body:
        content_type = (req.headers or {}).get("Content-Type", "") or (req.headers or {}).get("content-type", "")
        if "json" in content_type.lower() or req.body.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(req.body)
            except Exception:
                parsed = None
            if parsed is not None:
                for dotted_path, key, value in _json_leaves(parsed):
                    if isinstance(value, (str, int)) and (
                        looks_like_id_param(key) or looks_like_id_value(str(value))
                    ):
                        out.append(CandidateParam(
                            req, ParamLocation("json_body", key, str(value), json_path=dotted_path)
                        ))
        elif "x-www-form-urlencoded" in content_type.lower():
            for name, value in parse_qsl(req.body, keep_blank_values=True):
                if looks_like_id_param(name) or looks_like_id_value(value):
                    out.append(CandidateParam(req, ParamLocation("form_body", name, value)))

    # Dedup identical (location kind, name, value) pairs on the same request.
    seen = set()
    deduped = []
    for c in out:
        key = (c.location.kind, c.location.name, c.location.value, c.location.json_path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return deduped
