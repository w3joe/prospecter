"""Tavily-powered prospect research with per-worker rate limiting."""

from __future__ import annotations

import sys
import time
from collections import deque
from typing import Deque, List, Optional

from .models import Prospect, ResearchResult

_TAVILY_WINDOW_SECONDS = 600  # 10 minutes
_TAVILY_MAX_REQUESTS = 10     # per window per worker


class RateLimiter:
    """Track request timestamps and sleep when the limit would be exceeded."""

    def __init__(
        self,
        max_requests: int = _TAVILY_MAX_REQUESTS,
        window_seconds: float = _TAVILY_WINDOW_SECONDS,
    ) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._timestamps: Deque[float] = deque()

    def acquire(self) -> None:
        """Block until a request slot is available."""
        while True:
            now = time.monotonic()
            # Drop timestamps outside the window
            while self._timestamps and now - self._timestamps[0] >= self._window:
                self._timestamps.popleft()
            if len(self._timestamps) < self._max:
                self._timestamps.append(now)
                return
            # Must wait until the oldest timestamp falls outside the window
            sleep_for = self._window - (now - self._timestamps[0]) + 0.1
            time.sleep(sleep_for)


def _build_query(prospect: Prospect) -> str:
    parts = [prospect.name]
    if prospect.company:
        parts.append(prospect.company)
    return " ".join(parts)


def _summarise_results(results: list, prospect: Prospect) -> str:
    """Turn Tavily search results into structured research notes."""
    if not results:
        return f"No public information found for {prospect.display_name()}."
    lines: List[str] = [f"Research notes for {prospect.display_name()}:"]
    for item in results[:5]:
        title = item.get("title", "").strip()
        content = item.get("content", "").strip()
        url = item.get("url", "").strip()
        if title:
            lines.append(f"- {title}")
        if content:
            # Keep the first 300 characters of each snippet
            snippet = content[:300].replace("\n", " ")
            if len(content) > 300:
                snippet += "…"
            lines.append(f"  {snippet}")
        if url:
            lines.append(f"  Source: {url}")
    return "\n".join(lines)


def research_prospect(
    prospect: Prospect,
    api_key: str,
    rate_limiter: Optional[RateLimiter] = None,
    verbose: bool = False,
) -> ResearchResult:
    """Research a single prospect using the Tavily API.

    Args:
        prospect: The prospect to research.
        api_key: Tavily API key.
        rate_limiter: Optional shared rate limiter; created internally if not provided.
        verbose: If True, print progress to stderr.

    Returns:
        ResearchResult with notes (or an error message).
    """
    try:
        from tavily import TavilyClient  # type: ignore
    except ImportError as exc:
        return ResearchResult(
            prospect=prospect,
            notes="",
            error=f"tavily-python is not installed: {exc}",
        )

    if rate_limiter is None:
        rate_limiter = RateLimiter()

    query = _build_query(prospect)
    if verbose:
        print(
            f"[research] Waiting for rate limit slot for: {prospect.display_name()}",
            file=sys.stderr,
        )
    rate_limiter.acquire()

    if verbose:
        print(f"[research] Searching: {query!r}", file=sys.stderr)

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )
        raw = response.get("results", [])
        notes = _summarise_results(raw, prospect)
        # Prepend the Tavily answer if available
        answer = response.get("answer", "").strip()
        if answer:
            notes = f"Summary: {answer}\n\n{notes}"
        return ResearchResult(prospect=prospect, notes=notes, raw_results=raw)
    except Exception as exc:  # noqa: BLE001
        return ResearchResult(
            prospect=prospect,
            notes="",
            error=f"Research failed: {exc}",
        )
