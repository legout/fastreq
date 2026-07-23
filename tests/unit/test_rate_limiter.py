"""Tests for TokenBucket and AsyncRateLimiter.

The rate limiter is a pure token bucket — it does NOT own a semaphore.
Concurrency is owned by the client.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from fastreq.utils.rate_limiter import AsyncRateLimiter, RateLimitConfig, TokenBucket


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_token_refill(self) -> None:
        bucket = TokenBucket(requests_per_second=10, burst=5)
        bucket._tokens = 2
        bucket._last_update = time.monotonic()
        await asyncio.sleep(0.2)
        available = bucket.available()
        assert 3 <= available <= 5

    @pytest.mark.asyncio
    async def test_token_acquisition(self) -> None:
        bucket = TokenBucket(requests_per_second=10, burst=5)
        bucket._tokens = 3
        assert bucket.available() == 3
        await bucket.acquire(tokens=2)
        assert bucket.available() == 1

    @pytest.mark.asyncio
    async def test_wait_for_tokens(self) -> None:
        bucket = TokenBucket(requests_per_second=10, burst=5)
        bucket._tokens = 0
        start = time.monotonic()
        await bucket.acquire(tokens=1)
        elapsed = time.monotonic() - start
        assert 0.09 <= elapsed <= 0.15
        assert bucket.available() == 0

    @pytest.mark.asyncio
    async def test_query_available_tokens(self) -> None:
        bucket = TokenBucket(requests_per_second=10, burst=5)
        bucket._tokens = 3
        assert bucket.available() == 3

    @pytest.mark.asyncio
    async def test_burst_capacity(self) -> None:
        bucket = TokenBucket(requests_per_second=10, burst=3)
        bucket._tokens = 3
        await asyncio.sleep(0.5)
        assert bucket.available() == 3

    @pytest.mark.asyncio
    async def test_multiple_acquire_calls(self) -> None:
        bucket = TokenBucket(requests_per_second=10, burst=5)
        bucket._tokens = 5
        await bucket.acquire(tokens=2)
        assert bucket.available() == 3
        await bucket.acquire(tokens=1)
        assert bucket.available() == 2
        await bucket.acquire(tokens=2)
        assert bucket.available() == 0


class TestAsyncRateLimiter:
    def test_no_semaphore_in_rate_limiter(self) -> None:
        """Rate limiter does NOT own a concurrency semaphore."""
        config = RateLimitConfig(requests_per_second=10, burst=5)
        limiter = AsyncRateLimiter(config)
        assert not hasattr(limiter, "_semaphore")

    @pytest.mark.asyncio
    async def test_acquire_decrements_tokens(self) -> None:
        config = RateLimitConfig(requests_per_second=10, burst=5)
        limiter = AsyncRateLimiter(config)
        await limiter.acquire()
        assert limiter.available() == 4

    @pytest.mark.asyncio
    async def test_multiple_acquires(self) -> None:
        config = RateLimitConfig(requests_per_second=10, burst=5)
        limiter = AsyncRateLimiter(config)
        for _ in range(3):
            await limiter.acquire()
        assert limiter.available() == 2
