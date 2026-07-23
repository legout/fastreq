"""Tests for the FastRequests client public API.

Covers construction, request dispatch, return-type parsing, convenience
functions, and cookie management using the retained typed factory (no
importlib mocking, no removed backends).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest

from fastreq import (
    FastRequests,
    RequestOptions,
    ReturnType,
    fastreq_async,
)
from fastreq.backends.base import NormalizedResponse
from fastreq.exceptions import ConfigurationError, PartialFailureError
from tests.conftest import LocalTestServer, json_response


@pytest.fixture
async def server() -> AsyncIterator[LocalTestServer]:
    srv = LocalTestServer()
    await srv.start()
    yield srv
    await srv.stop()


class TestFastRequestsInit:
    def test_init_with_defaults(self) -> None:
        client = FastRequests()
        assert client.backend_name == "auto"
        assert client.concurrency == 20
        assert client.follow_redirects is True
        assert client.verify_ssl is True
        assert client.random_user_agent is True
        assert client.random_proxy is False
        assert client.debug is False
        assert client.verbose is True
        assert client.return_none_on_failure is False

    def test_init_with_custom_values(self) -> None:
        client = FastRequests(concurrency=10, http2=False)
        assert client.concurrency == 10
        assert client._http2 is False

    def test_init_with_rate_limit(self) -> None:
        client = FastRequests(rate_limit=100.0, rate_limit_burst=10, concurrency=5)
        assert client._rate_limiter is not None

    def test_init_without_rate_limit(self) -> None:
        client = FastRequests()
        assert client._rate_limiter is None

    def test_init_with_cookies(self) -> None:
        client = FastRequests(cookies={"session": "abc123"})
        assert client._cookies == {"session": "abc123"}

    def test_reset_cookies(self) -> None:
        client = FastRequests()
        client._cookies = {"session_id": "123"}
        client.reset_cookies()
        assert client._cookies == {}

    def test_set_cookies(self) -> None:
        client = FastRequests()
        client.set_cookies({"session_id": "123"})
        assert client._cookies == {"session_id": "123"}
        client.set_cookies({"user_id": "456"})
        assert client._cookies == {"session_id": "123", "user_id": "456"}

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self) -> None:
        client = FastRequests(backend="niquests", verbose=False)
        assert client._backend is not None
        async with client:
            assert client._backend is not None
        # After exit, backend sessions should be closed without error

    @pytest.mark.asyncio
    async def test_close_method(self) -> None:
        client = FastRequests(verbose=False)
        await client.close()  # Should not raise


class TestRequestOptions:
    def test_default_values(self) -> None:
        opts = RequestOptions(url="https://example.com")
        assert opts.url == "https://example.com"
        assert opts.method == "GET"
        assert opts.params is None
        assert opts.data is None
        assert opts.json is None
        assert opts.headers is None
        assert opts.timeout is None
        assert opts.proxy is None
        assert opts.return_type == ReturnType.JSON
        assert opts.stream_callback is None

    def test_custom_values(self) -> None:
        opts = RequestOptions(
            url="https://example.com",
            method="POST",
            params={"key": "value"},
            json={"data": "test"},
            headers={"Authorization": "Bearer token"},
            timeout=30.0,
            proxy="http://proxy.example.com:8080",
            return_type=ReturnType.TEXT,
        )
        assert opts.method == "POST"
        assert opts.params == {"key": "value"}
        assert opts.json == {"data": "test"}
        assert opts.headers == {"Authorization": "Bearer token"}
        assert opts.timeout == 30.0
        assert opts.proxy == "http://proxy.example.com:8080"
        assert opts.return_type == ReturnType.TEXT


class TestReturnType:
    def test_json_value(self) -> None:
        assert ReturnType.JSON.value == "json"

    def test_text_value(self) -> None:
        assert ReturnType.TEXT.value == "text"

    def test_content_value(self) -> None:
        assert ReturnType.CONTENT.value == "content"

    def test_response_value(self) -> None:
        assert ReturnType.RESPONSE.value == "response"

    def test_stream_value(self) -> None:
        assert ReturnType.STREAM.value == "stream"


class TestFastRequestsRequest:
    @pytest.mark.asyncio
    async def test_single_url_returns_single_result(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/api", json_response({"result": "success"}))
        client = FastRequests(verbose=False)
        async with client:
            result = await client.request(server.url("/api"))
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_multiple_urls_returns_list(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/a", json_response({"result": "a"}))
        server.add_route("GET", "/b", json_response({"result": "b"}))
        client = FastRequests(verbose=False)
        async with client:
            results = await client.request([server.url("/a"), server.url("/b")])
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0] == {"result": "a"}
        assert results[1] == {"result": "b"}

    @pytest.mark.asyncio
    async def test_urls_with_keys_returns_dict(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/a", json_response({"result": "first"}))
        server.add_route("GET", "/b", json_response({"result": "second"}))
        client = FastRequests(verbose=False)
        async with client:
            results = await client.request(
                [server.url("/a"), server.url("/b")],
                keys=["first", "second"],
            )
        assert isinstance(results, dict)
        assert results["first"] == {"result": "first"}
        assert results["second"] == {"result": "second"}

    @pytest.mark.asyncio
    async def test_keys_mismatch_raises_error(self) -> None:
        client = FastRequests(verbose=False)
        async with client:
            with pytest.raises(ConfigurationError) as exc_info:
                await client.request(
                    ["https://a.com", "https://b.com"],
                    keys=["only_one"],
                )
            assert "Number of keys" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_func_applied(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/api", json_response({"id": 123, "name": "test"}))
        client = FastRequests(verbose=False)
        async with client:
            result = await client.request(
                server.url("/api"),
                parse_func=lambda r: r.get("id"),
            )
        assert result == 123

    @pytest.mark.asyncio
    async def test_return_none_on_failure(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/ok", json_response({"result": "success"}))
        client = FastRequests(return_none_on_failure=True, verbose=False, max_retries=0)
        async with client:
            results = await client.request(
                [
                    server.url("/ok"),
                    "http://127.0.0.1:1/nonexistent",  # Will fail
                    server.url("/ok"),
                ]
            )
        assert len(results) == 3
        assert results[0] == {"result": "success"}
        assert results[1] is None
        assert results[2] == {"result": "success"}

    @pytest.mark.asyncio
    async def test_partial_failure_error(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/ok", json_response({"result": "success"}))
        client = FastRequests(return_none_on_failure=False, verbose=False, max_retries=0)
        async with client:
            with pytest.raises(PartialFailureError) as exc_info:
                await client.request(
                    [
                        server.url("/ok"),
                        "http://127.0.0.1:1/nonexistent",
                        server.url("/ok"),
                    ]
                )
        assert "1 of 3 requests failed" in str(exc_info.value)
        assert any("nonexistent" in url for url in exc_info.value.failures)

    @pytest.mark.asyncio
    async def test_return_type_as_string(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/api", json_response({"data": "result"}))
        client = FastRequests(verbose=False)
        async with client:
            result = await client.request(
                server.url("/api"),
                return_type="json",
            )
        assert result == {"data": "result"}

    @pytest.mark.asyncio
    async def test_timeout_override(self) -> None:
        client = FastRequests(timeout=10.0, verbose=False)
        async with client:
            await client.request("https://example.com", timeout=30.0)
        # No assertion needed — just verifying no error on override

    @pytest.mark.asyncio
    async def test_parse_response_json(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b'{"key": "value"}',
            url="https://example.com",
            is_json=True,
        )
        client = FastRequests(verbose=False)
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.JSON),
        )
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_parse_response_text(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "text/plain"},
            content=b"hello world",
            url="https://example.com",
            is_json=False,
        )
        client = FastRequests(verbose=False)
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.TEXT),
        )
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_parse_response_content(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/octet-stream"},
            content=b"binary data",
            url="https://example.com",
            is_json=False,
        )
        client = FastRequests(verbose=False)
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.CONTENT),
        )
        assert result == b"binary data"

    @pytest.mark.asyncio
    async def test_parse_response_response(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "text/plain"},
            content=b"hello",
            url="https://example.com",
            is_json=False,
        )
        client = FastRequests(verbose=False)
        result = client._parse_response(
            response,
            RequestOptions(url="https://example.com", return_type=ReturnType.RESPONSE),
        )
        assert result is response

    @pytest.mark.asyncio
    async def test_stream_parse_returns_none(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/zip"},
            content=b"chunk1chunk2chunk3",
            url="https://example.com/file.zip",
            is_json=False,
        )
        client = FastRequests(verbose=False)
        result = client._parse_response(
            response,
            RequestOptions(
                url="https://example.com/file.zip",
                return_type=ReturnType.STREAM,
            ),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_null_context(self) -> None:
        client = FastRequests(verbose=False)
        async with client._null_context():
            pass

    @pytest.mark.asyncio
    async def test_request_without_backend(self) -> None:
        client = FastRequests(verbose=False)
        client._backend = None
        with pytest.raises(ConfigurationError) as exc_info:
            async with client:
                await client.request("https://example.com")
        assert "Backend not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_request_without_backend(self) -> None:
        client = FastRequests(verbose=False)
        client._backend = None
        with pytest.raises(ConfigurationError) as exc_info:
            await client._execute_request(
                RequestOptions(url="https://example.com"),
                follow_redirects=True,
                verify_ssl=True,
            )
        assert "Backend not initialized" in str(exc_info.value)


class TestFastRequestsConvenienceFunctions:
    @pytest.mark.asyncio
    async def test_fastreq_async_wrapper(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/api", json_response({"result": "success"}))
        result = await fastreq_async(
            server.url("/api"),
            verbose=False,
        )
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_fastreq_async_single_url(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/api", json_response({"result": "success"}))
        result = await fastreq_async(server.url("/api"), verbose=False)
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_fastreq_async_with_keys(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/a", json_response({"id": "a"}))
        server.add_route("GET", "/b", json_response({"id": "b"}))
        result = await fastreq_async(
            [server.url("/a"), server.url("/b")],
            keys=["first", "second"],
            verbose=False,
        )
        assert result["first"] == {"id": "a"}
        assert result["second"] == {"id": "b"}


class TestFastRequestsRateLimiterIntegration:
    @pytest.mark.asyncio
    async def test_execute_request_with_rate_limiter(self) -> None:
        mock_response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b'{"result": "success"}',
            url="https://example.com",
            is_json=True,
        )
        client = FastRequests(rate_limit=10.0, rate_limit_burst=5, verbose=False)
        assert client._rate_limiter is not None
        assert client._backend is not None

        with patch.object(client._backend, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            async with client:
                result = await client.request(
                    "https://example.com/api",
                    return_type=ReturnType.JSON,
                )
            assert result == {"result": "success"}
