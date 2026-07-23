"""Retry policy with typed classification and exponential backoff.

Retries only transient transport failures (BackendError) and configured
retryable status codes (429, 500, 502, 503, 504). Honors Retry-After
header when parseable.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TypeVar

from loguru import logger

from ..exceptions import (
    BackendError,
    ConfigurationError,
    RetryableResponse,
    RetryExhaustedError,
    ValidationError,
)

# Type variable for the generic retry execute return type.
_T = TypeVar("_T")

# Status codes that are considered retryable
DEFAULT_RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})

# Exception types that should never be retried
NEVER_RETRY: tuple[type[Exception], ...] = (
    ConfigurationError,
    ValidationError,
)


@dataclass
class RetryConfig:
    """Configuration for retry strategy.

    Attributes:
        max_retries: Maximum number of retry attempts
        backoff_multiplier: Base multiplier for exponential backoff (seconds)
        jitter: Jitter amount as fraction of backoff (0.1 = 10%)
        retryable_statuses: HTTP status codes to retry (default: 429, 500, 502, 503, 504)
        max_delay: Maximum delay between retries (seconds, default 60)
    """

    max_retries: int = 3
    backoff_multiplier: float = 1.0
    jitter: float = 0.1
    retryable_statuses: frozenset[int] = field(default_factory=lambda: DEFAULT_RETRYABLE_STATUSES)
    max_delay: float = 60.0


class RetryStrategy:
    """Retry strategy with exponential backoff, jitter, and Retry-After support.

    Classifies failures as retryable or non-retryable:
    - BackendError (transport failure): retryable
    - RetryableResponse (429/5xx with status): retryable, honors Retry-After
    - ConfigurationError, ValidationError: never retry
    - Other exceptions: never retry

    Example:
        >>> config = RetryConfig(max_retries=3, backoff_multiplier=1.0)
        >>> strategy = RetryStrategy(config)
        >>> result = await strategy.execute(make_request_func)
    """

    def __init__(self, config: RetryConfig | None = None) -> None:
        self.config = config or RetryConfig()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt using exponential backoff with jitter.

        delay = min(max_delay, backoff_multiplier * (2^attempt) ± jitter)

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        base_delay = self.config.backoff_multiplier * (2**attempt)
        jitter_amount = self.config.jitter * base_delay
        jittered_delay = base_delay + random.uniform(-jitter_amount, jitter_amount)
        return float(max(0, min(self.config.max_delay, jittered_delay)))

    def _classify(self, error: Exception) -> tuple[bool, float | None]:
        """Classify an error and return (should_retry, retry_after_delay).

        Args:
            error: Exception that occurred

        Returns:
            Tuple of (should_retry, retry_after_seconds or None)
        """
        # Never retry configuration/validation errors
        if isinstance(error, NEVER_RETRY):
            return False, None

        # RetryableResponse carries a status code and optional Retry-After
        if isinstance(error, RetryableResponse):
            return True, error.retry_after

        # BackendError (transport failures) are retryable
        if isinstance(error, BackendError):
            return True, None

        # Unknown exceptions are not retried
        return False, None

    async def execute(
        self,
        func: Callable[..., Awaitable[_T]],
    ) -> _T:
        """Execute an async function with retry logic.

        Args:
            func: Async function to execute (no arguments)

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all retry attempts exhausted
            Exception: Original error if non-retryable
        """
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_error = e
                should_retry, retry_after = self._classify(e)

                if not should_retry:
                    raise

                if attempt < self.config.max_retries:
                    # Use Retry-After if available, otherwise exponential backoff
                    delay = (
                        retry_after if retry_after is not None else self._calculate_delay(attempt)
                    )
                    logger.debug(
                        f"Retry attempt {attempt + 1}/{self.config.max_retries}: {e}, "
                        f"waiting {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)

        logger.error(f"All retries exhausted after {self.config.max_retries} attempts")
        raise RetryExhaustedError(
            message=f"Retry attempts exhausted after {self.config.max_retries} retries",
            attempts=self.config.max_retries,
            last_error=last_error,
        )
