"""Thin async HTTP layer: send HttpRequest objects concurrently (bounded by
a semaphore), return HttpResponse objects. Centralizing this keeps rate
limiting, timeouts, and SSL handling in one place for every mutation
strategy.
"""
from __future__ import annotations

import asyncio
import time

import aiohttp

from .models import HttpRequest, HttpResponse


class Client:
    def __init__(self, concurrency: int = 10, timeout: float = 15.0,
                 verify_ssl: bool = True, delay: float = 0.0):
        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.verify_ssl = verify_ssl
        self.delay = delay
        self._sem = asyncio.Semaphore(concurrency)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "Client":
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, *exc):
        if self._session:
            await self._session.close()

    async def send(self, req: HttpRequest) -> HttpResponse:
        assert self._session is not None, "use `async with Client(...) as c:`"
        async with self._sem:
            start = time.monotonic()
            try:
                async with self._session.request(
                    req.method,
                    req.url,
                    headers=req.headers,
                    data=req.body.encode() if isinstance(req.body, str) else req.body,
                    ssl=self.verify_ssl,
                    allow_redirects=False,
                ) as resp:
                    body = await resp.text(errors="replace")
                    elapsed = (time.monotonic() - start) * 1000
                    if self.delay:
                        await asyncio.sleep(self.delay)
                    return HttpResponse(
                        status=resp.status,
                        headers=dict(resp.headers),
                        body=body,
                        elapsed_ms=elapsed,
                    )
            except asyncio.TimeoutError:
                return HttpResponse(status=0, error="timeout")
            except aiohttp.ClientError as e:
                return HttpResponse(status=0, error=str(e))

    async def send_many(self, requests: list[HttpRequest]) -> list[HttpResponse]:
        return await asyncio.gather(*(self.send(r) for r in requests))
