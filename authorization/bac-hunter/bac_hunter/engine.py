"""Wires parsing -> candidate extraction -> mutation strategies -> findings."""
from __future__ import annotations

import asyncio

from .client import Client
from .extract import extract_candidates
from .models import HttpRequest, Finding
from .mutations import STRATEGIES, MutationContext
from .sessions import Session


async def run(
    requests: list[HttpRequest],
    sessions: list[Session],
    strategy_names: list[str],
    concurrency: int = 10,
    timeout: float = 15.0,
    verify_ssl: bool = True,
    delay: float = 0.0,
    max_requests: int | None = None,
    progress_cb=None,
) -> list[Finding]:
    strategies = [STRATEGIES[name]() for name in strategy_names if name in STRATEGIES]
    if not strategies:
        raise ValueError(f"No valid strategies selected from {strategy_names}; available: {list(STRATEGIES)}")

    all_candidates = []
    for req in requests:
        all_candidates.extend(extract_candidates(req))

    if max_requests:
        all_candidates = all_candidates[:max_requests]

    findings: list[Finding] = []

    async with Client(concurrency=concurrency, timeout=timeout, verify_ssl=verify_ssl, delay=delay) as client:
        ctx = MutationContext(sessions=sessions, client=client, baseline_cache={})

        sem = asyncio.Semaphore(concurrency)

        async def run_one(candidate):
            async with sem:
                results = []
                for strategy in strategies:
                    try:
                        results.extend(await strategy.run(candidate, ctx))
                    except Exception as e:
                        # one bad candidate/strategy combo shouldn't kill the whole run
                        print(f"[!] {strategy.name} failed on "
                              f"{candidate.request.method} {candidate.request.path_and_query} "
                              f"param={candidate.location.name}: {e}")
                if progress_cb:
                    progress_cb()
                return results

        tasks = [run_one(c) for c in all_candidates]
        results_lists = await asyncio.gather(*tasks)
        for r in results_lists:
            findings.extend(r)

    findings.sort(key=lambda f: f.confidence_rank())
    return findings, len(all_candidates)
