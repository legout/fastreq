"""Tests for the request policy pipeline: rate limiting, retry, concurrency.

Covers:
- Token acquisition precedes concurrency acquisition (only one concurrency limit)
- Transport-error retry
- Retryable response statuses (429, 500, 502, 503, 504)
- Non-retryable 4xx handling
- Retry exhaustion
- Retry-After header parsing
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest

from fastreq import FastRequests, ReturnType
from fastreq.exceptions import (
    BackendError,
    ConfigurationError,
    RetryableResponse,
    RetryExhaustedError,
    ValidationError,
)
from fastreq.utils.retry import DEFAULT_RETRYABLE_STATUSES, RetryConfig, RetryStrategy
from tests.conftest import (
    LocalTestServer,
    MockResponse,
    json_response,
)


@pytest.fixture
async def server() -> AsyncIterator[LocalTestServer]:
    srv = LocalTestServer()
    await srv.start()
    yield srv
    await srv.stop()


class TestRateBeforeConcurrency:
    """Task 3.1, 3.2: Rate token acquisition precedes concurrency slot."""

    async def test_rate_acquired_before_concurrency(self) -> None:
        """A rate token is acquired before a concurrency slot is occupied."""
        order: list[str] = []
        client = FastRequests(
            rate_limit=10.0,
            rate_limit_burst=1,
            concurrency=1,
            max_retries=0,
            verbose=False,
        )

        # Instrument acquire ordering
        assert client._rate_limiter is not None
        original_rate_acquire = client._rate_limiter.acquire
        original_sem_acquire = client._concurrency_semaphore.acquire

        async def traced_rate() -> None:
            order.append("rate_start")
            await original_rate_acquire()
            order.append("rate_done")

        async def traced_sem() -> None:
            order.append("sem_start")
            await original_sem_acquire()
            order.append("sem_done")

        client._rate_limiter.acquire = traced_rate  # type: ignore[method-assign]
        client._concurrency_semaphore.acquire = traced_sem  # type: ignore[method-assign]

        # Run a request with a mocked backend
        from fastreq.backends.base import NormalizedResponse

        async def mock_request(config, stream_callback=None) -> NormalizedResponse:
            return NormalizedResponse(
                status_code=200,
                headers={},
                content=b'{"ok": true}',
                text='{"ok": true}',
                json_data={"ok": True},
                url=config.url,
                is_json=True,
            )

        async with client:
            client._backend.request = mock_request  # type: ignore[method-assign]
            await client.request("http://example.com/test")

        # rate_start must come before sem_start
        assert order.index("rate_start") < order.index("sem_start")

    async def test_only_one_concurrency_limit(self) -> None:
        """There is exactly one concurrency gate per client."""
        client = FastRequests(concurrency=5, verbose=False)
        assert client._concurrency_semaphore is not None
        assert client._concurrency_semaphore._value == 5

        # Rate limiter does NOT have its own semaphore
        client_with_rate = FastRequests(concurrency=3, rate_limit=10.0, verbose=False)
        assert client_with_rate._concurrency_semaphore is not None
        assert client_with_rate._concurrency_semaphore._value == 3
        # Rate limiter should NOT have an internal semaphore
        assert not hasattr(client_with_rate._rate_limiter, "_semaphore")


class TestRetryClassification:
    """Task 3.3, 3.4: Retry classifier behavior."""

    def test_backend_error_is_retryable(self) -> None:
        strategy = RetryStrategy(RetryConfig(max_retries=2))
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

    async def test_transport_error_retries_then_succeeds(self) -> None:
        """A transport error that later resolves should retry."""
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

    async def test_retry_exhausted_raises(self) -> None:
        """When all retries fail, RetryExhaustedError is raised."""

        async def always_fail() -> None:
            raise BackendError("always fails")

        strategy = RetryStrategy(RetryConfig(max_retries=2, backoff_multiplier=0.01))
        with pytest.raises(RetryExhaustedError):
            await strategy.execute(always_fail)

    async def test_non_retryable_raises_immediately(self) -> None:
        """ConfigurationError is raised without retry."""
        call_count = 0

        async def bad_config() -> None:
            nonlocal call_count
            call_count += 1
            raise ConfigurationError("bad")

        strategy = RetryStrategy()
        with pytest.raises(ConfigurationError):
            await strategy.execute(bad_config)
        assert call_count == 1  # Not retried

    async def test_retry_after_delay_used(self) -> None:
        """RetryableResponse with retry_after uses that delay."""
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

        with patch("fastreq.utils.retry.asyncio.sleep", traced_sleep):
            strategy = RetryStrategy(RetryConfig(max_retries=1))
            result = await strategy.execute(rate_limited)

        assert result == "ok"
        assert len(delays) == 1
        assert delays[0] == 0.01  # retry_after was used


class TestRetryableStatusCodes:
    """Test retry behavior for HTTP status codes with real server."""

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_500_retries_and_succeeds(self, backend: str, server: LocalTestServer) -> None:
        """A 500 that later returns 200 should retry and succeed."""
        call_count = 0

        def handler() -> MockResponse:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return MockResponse(status=500, body=b"error")
            return json_response({"ok": True})

        server.add_route("GET", "/flaky", handler)

        client = FastRequests(
            backend=backend,
            max_retries=2,
            verbose=False,
        )
        # Override retry config with fast backoff for test speed
        from fastreq.utils.retry import RetryConfig

        client._retry_strategy = RetryStrategy(RetryConfig(max_retries=2, backoff_multiplier=0.01))
        async with client:
            result = await client.request(
                server.url("/flaky"),
                return_type=ReturnType.JSON,
            )
        assert result == {"ok": True}
        assert call_count == 2

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_404_not_retried(self, backend: str, server: LocalTestServer) -> None:
        """A 404 is not retried."""
        call_count = 0

        def handler() -> MockResponse:
            nonlocal call_count
            call_count += 1
            return MockResponse(status=404, body=b"Not Found")

        server.add_route("GET", "/missing", handler)

        client = FastRequests(
            backend=backend,
            max_retries=3,
            verbose=False,
            return_none_on_failure=True,
        )
        async with client:
            result = await client.request(
                server.url("/missing"),
                return_type=ReturnType.RESPONSE,
            )
        # 404 is returned as a normal response (not retried)
        assert result is not None
        assert result.status_code == 404
        assert call_count == 1

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_429_retries_and_succeeds(self, backend: str, server: LocalTestServer) -> None:
        """A 429 with Retry-After should retry and succeed."""
        call_count = 0

        def handler() -> MockResponse:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return MockResponse(
                    status=429,
                    body=b"rate limited",
                    headers={"Retry-After": "0"},
                )
            return json_response({"ok": True})

        server.add_route("GET", "/limited", handler)

        client = FastRequests(
            backend=backend,
            max_retries=2,
            verbose=False,
        )
        async with client:
            result = await client.request(
                server.url("/limited"),
                return_type=ReturnType.JSON,
            )
        assert result == {"ok": True}
        assert call_count == 2

    async def test_configuration_error_not_retried_via_client(
        self, server: LocalTestServer
    ) -> None:
        """Configuration errors do not retry."""
        server.add_route("GET", "/data", json_response({"ok": True}))

        client = FastRequests(
            backend="niquests",
            max_retries=3,
            verbose=False,
        )

        # Verify keys validation raises without retry
        async with client:
            with pytest.raises(ConfigurationError):
                await client.request(
                    ["http://a", "http://b"],
                    keys=["only_one"],
                )
