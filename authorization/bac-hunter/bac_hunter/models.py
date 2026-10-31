"""Core data structures shared across the tool."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlsplit, parse_qsl

# Param names that look like object/user/org identifiers worth mutating.
ID_PARAM_NAME_RE = re.compile(
    r"(?:^|_|-)(id|uuid|guid|user_?id|account_?id|org(?:anization)?_?id|"
    r"owner_?id|customer_?id|order_?id|invoice_?id|ticket_?id|project_?id|"
    r"tenant_?id|team_?id|file_?id|doc(?:ument)?_?id|session_?id|token_?id|"
    r"uid|pk)(?:$|_|-)",
    re.IGNORECASE,
)

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
NUMERIC_ID_RE = re.compile(r"^\d{1,19}$")
MONGO_OID_RE = re.compile(r"^[0-9a-f]{24}$", re.IGNORECASE)


def looks_like_id_value(value: str) -> bool:
    if not value:
        return False
    return bool(UUID_RE.match(value) or NUMERIC_ID_RE.match(value) or MONGO_OID_RE.match(value))


def looks_like_id_param(name: str) -> bool:
    return bool(ID_PARAM_NAME_RE.search(name))


@dataclass
class ParamLocation:
    """Where a candidate identifier param was found in a request."""
    kind: str  # "query" | "path" | "json_body" | "form_body" | "header"
    name: str
    value: str
    # For JSON bodies, the dotted path to the field, e.g. "data.owner.id"
    json_path: Optional[str] = None


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: Optional[str] = None  # raw body string, if any
    source: str = ""  # which export/line this came from, for traceability

    @property
    def path_and_query(self) -> str:
        parts = urlsplit(self.url)
        return parts.path + (("?" + parts.query) if parts.query else "")

    def query_params(self) -> list[tuple[str, str]]:
        parts = urlsplit(self.url)
        return parse_qsl(parts.query, keep_blank_values=True)

    def clone(self) -> "HttpRequest":
        return HttpRequest(
            method=self.method,
            url=self.url,
            headers=dict(self.headers),
            body=self.body,
            source=self.source,
        )


@dataclass
class HttpResponse:
    status: int
    headers: dict = field(default_factory=dict)
    body: str = ""
    elapsed_ms: float = 0.0
    error: Optional[str] = None  # set if the request failed (timeout, conn error)

    @property
    def body_len(self) -> int:
        return len(self.body or "")


@dataclass
class CandidateParam:
    """An identifier-looking parameter extracted from a request, ready to mutate."""
    request: HttpRequest
    location: ParamLocation


@dataclass
class Finding:
    strategy: str  # name of the mutation strategy that produced this
    description: str
    confidence: str  # "high" | "medium" | "low"
    baseline_request: HttpRequest
    baseline_response: HttpResponse
    mutated_request: HttpRequest
    mutated_response: HttpResponse
    notes: str = ""

    def confidence_rank(self) -> int:
        return {"high": 0, "medium": 1, "low": 2}.get(self.confidence, 3)
