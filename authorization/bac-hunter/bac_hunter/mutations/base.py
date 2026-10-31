"""The plugin contract for mutation strategies. Add a new module in this
package, subclass MutationStrategy, and register it in mutations/__init__.py
-- the engine will pick it up automatically.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..client import Client
from ..models import CandidateParam, Finding, HttpResponse
from ..sessions import Session


@dataclass
class MutationContext:
    sessions: list[Session]           # all configured privilege levels, low->high
    client: Client
    baseline_cache: dict               # shared cache: baseline_key -> HttpResponse


class MutationStrategy(ABC):
    """One angle of attack: given a candidate param (an endpoint+identifier
    pulled from the import), produce mutated requests, send them, and decide
    which responses are worth flagging as findings.
    """
    name: str = "base"

    @abstractmethod
    async def run(self, candidate: CandidateParam, ctx: MutationContext) -> list[Finding]:
        ...

    @staticmethod
    def is_suspicious(baseline: HttpResponse, mutated: HttpResponse) -> tuple[bool, str, str]:
        """Shared heuristic: does `mutated` look like it leaked data that
        `baseline` (the expected-denied case) did not?
        Returns (flagged, confidence, reason).
        """
        if mutated.error:
            return False, "low", f"request error: {mutated.error}"

        # The headline case: baseline denied (403/404/401), mutated succeeded with a body.
        if baseline.status in (401, 403, 404) and mutated.status == 200 and mutated.body_len > 0:
            return True, "high", (
                f"baseline denied ({baseline.status}) but mutated request returned 200 "
                f"with {mutated.body_len} bytes of body"
            )

        # Both "succeeded" but body sizes differ a lot - could mean the mutated
        # request got a *different* object's data rather than a clean 403.
        if baseline.status == 200 and mutated.status == 200:
            if baseline.body_len == 0 and mutated.body_len > 0:
                return True, "medium", "baseline had empty 200 body, mutated returned data"
            if baseline.body_len > 0:
                if mutated.body == baseline.body:
                    # A *different* identity/object got the exact same payload back -
                    # strongest possible anomaly-diff signal, regardless of size.
                    return True, "high", (
                        "mutated request returned 200 with a BYTE-IDENTICAL body to the "
                        "baseline - the endpoint returned the same protected object to a "
                        "different identity/parameter"
                    )
                diff_ratio = abs(mutated.body_len - baseline.body_len) / max(baseline.body_len, 1)
                if diff_ratio > 0.15:
                    return True, "low", (
                        f"both 200 but body length differs by {diff_ratio:.0%} "
                        "(may just be different legitimate data - verify manually)"
                    )

        return False, "low", ""
