"""Token bucket rate limiting.

The client owns one concurrency gate (semaphore) and one token bucket.
Rate token acquisition happens BEFORE the concurrency slot is occupied,
ensuring that a request waiting for a rate token does not block a
concurrency slot that could serve another request.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from loguru import logger


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        requests_per_second: Maximum requests per second
        burst: Maximum burst size (tokens)
    """

    requests_per_second: float
    burst: int


class TokenBucket:
    """Token bucket algorithm for rate limiting.

    Implements the token bucket algorithm to control request rate with
    burst capability.

    Args:
        requests_per_second: Token refill rate
        burst: Maximum bucket size (tokens)
    """

    def __init__(self, requests_per_second: float, burst: int) -> None:
        self.requests_per_second = requests_per_second
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now
        self._tokens = min(self.burst, self._tokens + elapsed * self.requests_per_second)

    def available(self) -> int:
        """Get available tokens.

        Returns:
            Number of tokens currently available
        """
        self._refill_tokens()
        return int(self._tokens)

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire
        """
        while True:
            self._refill_tokens()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            wait_time = (tokens - self._tokens) / self.requests_per_second
            logger.debug(f"Rate limit: waiting {wait_time:.3f}s for token")
            await asyncio.sleep(wait_time)


class AsyncRateLimiter:
    """Async rate limiter using token bucket algorithm.

    This is a pure token-bucket rate limiter. It does NOT manage concurrency —
    concurrency is owned by the client via its own semaphore.

    The client acquires a rate token BEFORE acquiring a concurrency slot,
    ensuring rate-limit-waiting requests don't occupy slots.

    Args:
        config: Rate limiting configuration
    """

    def __init__(self, config: RateLimitConfig) -> None:
        self.config = config
        self._bucket = TokenBucket(config.requests_per_second, config.burst)

    async def acquire(self) -> None:
        """Acquire a rate token, waiting if necessary."""
        await self._bucket.acquire()

    def available(self) -> int:
        """Get available tokens.

        Returns:
            Number of tokens currently available
        """
        return self._bucket.available()
