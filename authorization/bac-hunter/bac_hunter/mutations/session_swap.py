"""Strategy 1: keep the original object ID, swap in every OTHER session's
auth. Catches both horizontal IDOR (same level, different user's object)
and vertical privilege escalation (lower-privileged session reaching a
higher-privileged object), depending on how you set up your session levels.
"""
from __future__ import annotations

from ..models import CandidateParam, Finding
from .base import MutationStrategy, MutationContext


class SessionSwapStrategy(MutationStrategy):
    name = "session_swap"

    async def run(self, candidate: CandidateParam, ctx: MutationContext) -> list[Finding]:
        req = candidate.request
        findings: list[Finding] = []

        baseline_key = ("baseline", req.method, req.url, req.body)
        if baseline_key not in ctx.baseline_cache:
            ctx.baseline_cache[baseline_key] = await ctx.client.send(req)
        baseline = ctx.baseline_cache[baseline_key]

        owner_session = _guess_owner_session(req, ctx.sessions)

        for session in ctx.sessions:
            if owner_session and session.name == owner_session.name:
                continue  # skip replaying with the same identity that made the baseline

            mutated_req = req.clone()
            mutated_req.headers = session.apply(req.headers)
            mutated_resp = await ctx.client.send(mutated_req)

            flagged, confidence, reason = self.is_suspicious(baseline, mutated_resp)
            if flagged:
                direction = "vertical" if owner_session and session.level != owner_session.level else "horizontal"
                findings.append(Finding(
                    strategy=self.name,
                    description=(
                        f"{direction} access: object identified by {candidate.location.kind} "
                        f"param '{candidate.location.name}'={candidate.location.value!r} on "
                        f"{req.method} {req.path_and_query} was reachable using session "
                        f"'{session.name}' (level {session.level})"
                    ),
                    confidence=confidence,
                    baseline_request=req,
                    baseline_response=baseline,
                    mutated_request=mutated_req,
                    mutated_response=mutated_resp,
                    notes=reason,
                ))

        return findings


def _guess_owner_session(req, sessions):
    """If the request's own auth header matches a configured session, treat
    that as the 'owner' identity so we don't replay against itself and so
    we can label vertical vs horizontal findings.
    """
    cookie = (req.headers or {}).get("Cookie", "") or (req.headers or {}).get("cookie", "")
    auth = (req.headers or {}).get("Authorization", "") or (req.headers or {}).get("authorization", "")
    for s in sessions:
        if s.cookie and s.cookie in cookie:
            return s
        if s.bearer and s.bearer in auth:
            return s
    return None
