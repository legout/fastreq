"""Tests for the typed retry classifier and RetryStrategy.

Covers:
- Exponential backoff delay calculation with jitter
- Typed error classification (retryable vs non-retryable)
- Max-retries enforcement
- Retry-After delay usage
- Non-retryable errors raised immediately
"""

from __future__ import annotations

import asyncio

import pytest

from fastreq.exceptions import (
    BackendError,
    ConfigurationError,
    RetryableResponse,
    RetryExhaustedError,
    ValidationError,
)
from fastreq.utils.retry import (
    DEFAULT_RETRYABLE_STATUSES,
    RetryConfig,
    RetryStrategy,
)


class TestDelayCalculation:
    def test_exponential_delay_no_jitter(self) -> None:
        strategy = RetryStrategy(RetryConfig(max_retries=3, backoff_multiplier=1.0, jitter=0.0))
        assert strategy._calculate_delay(0) == 1.0
        assert strategy._calculate_delay(1) == 2.0
        assert strategy._calculate_delay(2) == 4.0

    def test_jitter_within_bounds(self) -> None:
        strategy = RetryStrategy(RetryConfig(max_retries=3, backoff_multiplier=1.0, jitter=0.1))
        delays = [strategy._calculate_delay(0) for _ in range(100)]
        assert len(set(delays)) > 1
        for delay in delays:
            assert 0.9 <= delay <= 1.1

    def test_max_delay_cap(self) -> None:
        strategy = RetryStrategy(
            RetryConfig(max_retries=10, backoff_multiplier=100.0, max_delay=50.0, jitter=0.0)
        )
        delay = strategy._calculate_delay(5)
        assert delay == 50.0


class TestErrorClassification:
    def test_backend_error_is_retryable(self) -> None:
        strategy = RetryStrategy()
        should, delay = strategy._classify(BackendError("timeout"))
        assert should is True
        assert delay is None

    def test_configuration_error_not_retryable(self) -> None:
        strategy = RetryStrategy()
        should, _ = strategy._classify(ConfigurationError("bad config"))
        assert should is False

    def test_validation_error_not_retryable(self) -> None:
        strategy = RetryStrategy()
        should, _ = strategy._classify(ValidationError("bad input"))
        assert should is False

    def test_retryable_response_is_retryable(self) -> None:
        strategy = RetryStrategy()
        should, delay = strategy._classify(
            RetryableResponse("429", status_code=429, retry_after=5.0)
        )
        assert should is True
        assert delay == 5.0

    def test_unknown_exception_not_retryable(self) -> None:
        strategy = RetryStrategy()
        should, _ = strategy._classify(ValueError("random"))
        assert should is False

    def test_default_retryable_statuses(self) -> None:
        assert 429 in DEFAULT_RETRYABLE_STATUSES
        assert 500 in DEFAULT_RETRYABLE_STATUSES
        assert 502 in DEFAULT_RETRYABLE_STATUSES
        assert 503 in DEFAULT_RETRYABLE_STATUSES
        assert 504 in DEFAULT_RETRYABLE_STATUSES
        assert 400 not in DEFAULT_RETRYABLE_STATUSES
        assert 404 not in DEFAULT_RETRYABLE_STATUSES


class TestRetryExecution:
    @pytest.mark.asyncio
    async def test_transport_error_retries_then_succeeds(self) -> None:
        call_count = 0

        async def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise BackendError("timeout")
            return "success"

        strategy = RetryStrategy(RetryConfig(max_retries=3, backoff_multiplier=0.01))
        result = await strategy.execute(flaky_func)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self) -> None:
        async def always_fail() -> None:
            raise BackendError("always fails")

        strategy = RetryStrategy(RetryConfig(max_retries=2, backoff_multiplier=0.01))
        with pytest.raises(RetryExhaustedError):
            await strategy.execute(always_fail)

    @pytest.mark.asyncio
    async def test_non_retryable_raises_immediately(self) -> None:
        call_count = 0

        async def bad_config() -> None:
            nonlocal call_count
            call_count += 1
            raise ConfigurationError("bad")

        strategy = RetryStrategy()
        with pytest.raises(ConfigurationError):
            await strategy.execute(bad_config)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_after_delay_used(self) -> None:
        call_count = 0
        delays: list[float] = []

        async def rate_limited() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RetryableResponse("429", status_code=429, retry_after=0.01)
            return "ok"

        original_sleep = asyncio.sleep

        async def traced_sleep(delay: float) -> None:
            delays.append(delay)
            await original_sleep(delay)

        with pytest.MonkeyPatch().context() as m:
            m.setattr("fastreq.utils.retry.asyncio.sleep", traced_sleep)
            strategy = RetryStrategy(RetryConfig(max_retries=1))
            result = await strategy.execute(rate_limited)

        assert result == "ok"
        assert len(delays) == 1
        assert delays[0] == 0.01

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self) -> None:
        call_count = 0

        async def good_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        strategy = RetryStrategy(RetryConfig(max_retries=3))
        result = await strategy.execute(good_func)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_exhaustion_count(self) -> None:
        call_count = 0

        async def always_fail() -> None:
            nonlocal call_count
            call_count += 1
            raise BackendError("fail")

        strategy = RetryStrategy(RetryConfig(max_retries=2, backoff_multiplier=0.01))
        with pytest.raises(RetryExhaustedError) as exc_info:
            await strategy.execute(always_fail)

        assert call_count == 3  # initial + 2 retries
        assert exc_info.value.attempts == 2
        assert isinstance(exc_info.value.last_error, BackendError)

    @pytest.mark.asyncio
    async def test_default_retry_config(self) -> None:
        strategy = RetryStrategy()
        assert strategy.config.max_retries == 3
        assert strategy.config.backoff_multiplier == 1.0
        assert strategy.config.jitter == 0.1
