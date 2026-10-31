"""Render findings as Markdown or JSON, ranked by confidence, with the full
request/response pairs so you can paste straight into a writeup.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from .models import Finding, HttpRequest, HttpResponse

MAX_BODY_PREVIEW = 1500


def _truncate(s: str, n: int = MAX_BODY_PREVIEW) -> str:
    if s is None:
        return ""
    if len(s) <= n:
        return s
    return s[:n] + f"\n... [truncated, {len(s)} bytes total]"


def _req_block(req: HttpRequest) -> str:
    lines = [f"{req.method} {req.url}"]
    for k, v in (req.headers or {}).items():
        lines.append(f"{k}: {v}")
    if req.body:
        lines.append("")
        lines.append(_truncate(req.body))
    return "\n".join(lines)


def _resp_block(resp: HttpResponse) -> str:
    if resp.error:
        return f"[request error: {resp.error}]"
    lines = [f"HTTP {resp.status}  ({resp.elapsed_ms:.0f} ms, {resp.body_len} bytes)"]
    for k, v in list((resp.headers or {}).items())[:15]:
        lines.append(f"{k}: {v}")
    lines.append("")
    lines.append(_truncate(resp.body))
    return "\n".join(lines)


def to_markdown(findings: list[Finding], candidates_tested: int, target_label: str = "") -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[f.confidence] = counts.get(f.confidence, 0) + 1

    lines = [
        f"# bac-hunter report{': ' + target_label if target_label else ''}",
        "",
        f"Generated: {now}",
        f"Candidate params tested: {candidates_tested}",
        f"Findings: {len(findings)}  (high: {counts['high']}, medium: {counts['medium']}, low: {counts['low']})",
        "",
        "All findings below need manual verification before writeup/submission - this tool flags",
        "anomalies, it does not confirm exploitability.",
        "",
    ]

    for i, f in enumerate(findings, 1):
        lines.append(f"## [{f.confidence.upper()}] Finding {i}: {f.strategy}")
        lines.append("")
        lines.append(f.description)
        if f.notes:
            lines.append(f"\n_Reason flagged: {f.notes}_")
        lines.append("")
        lines.append("<details><summary>Baseline request/response</summary>\n")
        lines.append("```http")
        lines.append(_req_block(f.baseline_request))
        lines.append("```")
        lines.append("```http")
        lines.append(_resp_block(f.baseline_response))
        lines.append("```")
        lines.append("</details>\n")
        lines.append("<details><summary>Mutated request/response (the flagged one)</summary>\n")
        lines.append("```http")
        lines.append(_req_block(f.mutated_request))
        lines.append("```")
        lines.append("```http")
        lines.append(_resp_block(f.mutated_response))
        lines.append("```")
        lines.append("</details>\n")
        lines.append("---\n")

    if not findings:
        lines.append("No anomalies flagged. Either the app is solid on the tested params, or the "
                      "candidate set/strategies need broadening - check the extracted param list.")

    return "\n".join(lines)


def to_json(findings: list[Finding], candidates_tested: int, target_label: str = "") -> str:
    def req_dict(r: HttpRequest) -> dict:
        return {"method": r.method, "url": r.url, "headers": r.headers, "body": r.body}

    def resp_dict(r: HttpResponse) -> dict:
        return {
            "status": r.status, "headers": r.headers, "body": _truncate(r.body),
            "elapsed_ms": r.elapsed_ms, "error": r.error,
        }

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "target": target_label,
        "candidates_tested": candidates_tested,
        "finding_count": len(findings),
        "findings": [
            {
                "strategy": f.strategy,
                "confidence": f.confidence,
                "description": f.description,
                "notes": f.notes,
                "baseline_request": req_dict(f.baseline_request),
                "baseline_response": resp_dict(f.baseline_response),
                "mutated_request": req_dict(f.mutated_request),
                "mutated_response": resp_dict(f.mutated_response),
            }
            for f in findings
        ],
    }
    return json.dumps(out, indent=2)
