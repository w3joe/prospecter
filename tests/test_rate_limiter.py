"""Tests for the rate limiter."""

from __future__ import annotations

import time

from depthreach.researcher import RateLimiter


class TestRateLimiter:
    def test_allows_requests_within_limit(self):
        rl = RateLimiter(max_requests=5, window_seconds=60)
        # Should allow 5 requests without sleeping
        start = time.monotonic()
        for _ in range(5):
            rl.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"Expected fast completion, got {elapsed:.2f}s"

    def test_blocks_when_limit_exceeded(self):
        # With a tiny window and max=1, the second request should block
        rl = RateLimiter(max_requests=1, window_seconds=0.3)
        rl.acquire()  # use up the slot
        start = time.monotonic()
        rl.acquire()  # should wait ~0.3s
        elapsed = time.monotonic() - start
        assert elapsed >= 0.25, f"Expected ~0.3s sleep, got {elapsed:.2f}s"
