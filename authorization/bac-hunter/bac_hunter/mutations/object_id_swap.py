"""Strategy 2: keep the original request's own auth, swap only the object
ID. Classic IDOR shape - same session, different object.

Candidate replacement IDs come from, in priority order:
  1. Any `object_ids` declared on OTHER sessions in the config (highest
     confidence - these are real IDs known to belong to someone else).
  2. For purely numeric IDs, +1/-1 neighbors as a best-effort guess if no
     object_ids were configured (lower confidence - flagged but needs
     manual verification, since a neighboring ID might not exist at all).
"""
from __future__ import annotations

from ..models import CandidateParam, Finding, looks_like_id_value
from ..rebuild import with_param_value
from .base import MutationStrategy, MutationContext


class ObjectIdSwapStrategy(MutationStrategy):
    name = "object_id_swap"

    async def run(self, candidate: CandidateParam, ctx: MutationContext) -> list[Finding]:
        req = candidate.request
        loc = candidate.location
        if not looks_like_id_value(loc.value):
            return []  # name looked ID-ish but value doesn't (e.g. "current"); skip guessing

        baseline_key = ("baseline", req.method, req.url, req.body)
        if baseline_key not in ctx.baseline_cache:
            ctx.baseline_cache[baseline_key] = await ctx.client.send(req)
        baseline = ctx.baseline_cache[baseline_key]

        candidates = self._candidate_values(loc.value, ctx)
        findings: list[Finding] = []

        for new_value, source_confidence in candidates:
            if new_value == loc.value:
                continue
            mutated_req = with_param_value(req, loc, new_value)
            mutated_resp = await ctx.client.send(mutated_req)

            flagged, confidence, reason = self.is_suspicious(baseline, mutated_resp)

            # A known-to-belong-to-someone-else object ID, fetched with the SAME
            # session, that comes back 200 with data is itself the IDOR - no
            # need for a denied baseline or a big size delta to call this out.
            if not flagged and source_confidence == "known" and mutated_resp.status == 200 \
                    and mutated_resp.body_len > 0:
                flagged, confidence = True, "high"
                reason = (
                    f"same session fetched object id {new_value!r}, which is declared in the "
                    "config as belonging to a DIFFERENT session, and got a 200 with data back"
                )

            if flagged:
                # downgrade confidence if the replacement id was only guessed
                if source_confidence == "guessed" and confidence == "high":
                    confidence = "medium"
                findings.append(Finding(
                    strategy=self.name,
                    description=(
                        f"IDOR candidate: {req.method} {req.path_and_query} - param "
                        f"'{loc.name}' swapped {loc.value!r} -> {new_value!r} "
                        f"({source_confidence} replacement id) using the SAME session"
                    ),
                    confidence=confidence,
                    baseline_request=req,
                    baseline_response=baseline,
                    mutated_request=mutated_req,
                    mutated_response=mutated_resp,
                    notes=reason,
                ))

        return findings

    @staticmethod
    def _candidate_values(original: str, ctx: MutationContext) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for session in ctx.sessions:
            for oid in session.object_ids:
                if oid != original:
                    out.append((oid, "known"))

        if not out and original.isdigit():
            n = int(original)
            out.append((str(n + 1), "guessed"))
            if n > 0:
                out.append((str(n - 1), "guessed"))

        return out
