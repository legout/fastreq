"""Shared hermetic contract tests for both retained transports.

Tests that both niquests and httpx backends satisfy the same transport
contract: normal requests, JSON normalization, redirects, headers,
cookies, TLS config delegation, and streaming.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from fastreq import FastRequests, ReturnType
from tests.conftest import (
    LocalTestServer,
    MockResponse,
    chunked_response,
    json_response,
    text_response,
)

# Backends under contract. curl_cffi is optional; include it when installed.
_BACKENDS = ["niquests", "httpx"]
try:
    import curl_cffi  # noqa: F401

    _BACKENDS.append("curl_cffi")
except ImportError:
    pass


@pytest.fixture
async def server() -> AsyncIterator[LocalTestServer]:
    """Start a local test server for each test."""
    srv = LocalTestServer()
    await srv.start()
    yield srv
    await srv.stop()


@pytest.fixture
async def make_client():
    """Factory for creating and cleaning up FastRequests clients.

    Cleanup runs in the test's own event loop — some transports (curl_cffi)
    bind sessions to the loop that created them.
    """
    clients: list[FastRequests] = []

    async def _create(backend: str = "auto", **kwargs) -> FastRequests:
        client = FastRequests(backend=backend, **kwargs)
        await client.__aenter__()
        clients.append(client)
        return client

    yield _create

    for c in clients:
        await c.close()


class TestTransportContract:
    """Contract tests that must pass for BOTH niquests and httpx backends."""

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_normal_json_request(
        self, backend: str, server: LocalTestServer, make_client
    ) -> None:
        """Both transports return a normalized JSON response."""
        server.add_route("GET", "/api", json_response({"key": "value"}))
        client = await make_client(backend, verbose=False)
        result = await client.request(
            server.url("/api"),
            return_type=ReturnType.JSON,
        )
        assert result == {"key": "value"}

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_text_response(self, backend: str, server: LocalTestServer, make_client) -> None:
        """Both transports return text content."""
        server.add_route("GET", "/text", text_response("hello world"))
        client = await make_client(backend, verbose=False)
        result = await client.request(
            server.url("/text"),
            return_type=ReturnType.TEXT,
        )
        assert result == "hello world"

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_content_bytes(self, backend: str, server: LocalTestServer, make_client) -> None:
        """Both transports return raw bytes."""
        server.add_route("GET", "/raw", MockResponse(body=b"\x00\x01\x02\x03"))
        client = await make_client(backend, verbose=False)
        result = await client.request(
            server.url("/raw"),
            return_type=ReturnType.CONTENT,
        )
        assert result == b"\x00\x01\x02\x03"

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_response_object(
        self, backend: str, server: LocalTestServer, make_client
    ) -> None:
        """Both transports return a NormalizedResponse object."""
        server.add_route("GET", "/resp", json_response({"ok": True}))
        client = await make_client(backend, verbose=False)
        result = await client.request(
            server.url("/resp"),
            return_type=ReturnType.RESPONSE,
        )
        assert result.status_code == 200
        assert result.is_json
        assert result.json_data == {"ok": True}

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_post_json_body(self, backend: str, server: LocalTestServer, make_client) -> None:
        """Both transports can POST JSON bodies."""
        server.add_route("POST", "/echo", json_response({"received": True}))
        client = await make_client(backend, verbose=False)
        result = await client.request(
            server.url("/echo"),
            method="POST",
            json={"data": 42},
            return_type=ReturnType.JSON,
        )
        assert result == {"received": True}

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_status_code_passthrough(
        self, backend: str, server: LocalTestServer, make_client
    ) -> None:
        """Both transports pass through HTTP status codes."""
        server.add_route("GET", "/error", MockResponse(status=404, body=b"Not Found"))
        client = await make_client(backend, verbose=False, return_none_on_failure=True)
        result = await client.request(
            server.url("/error"),
            return_type=ReturnType.RESPONSE,
        )
        assert result is not None
        assert result.status_code == 404

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_cookies_sent(self, backend: str, server: LocalTestServer, make_client) -> None:
        """Both transports send session cookies."""
        server.add_route("GET", "/cookie", json_response({"ok": True}))
        client = await make_client(backend, verbose=False)
        client.set_cookies({"test_cookie": "abc123"})
        await client.request(server.url("/cookie"))
        # Verify the server received the cookie
        last_request = server.requests_received[-1]
        req_headers: dict[str, object] = last_request["headers"]  # type: ignore[assignment]
        cookie_header = req_headers.get("cookie", "")
        assert "test_cookie=abc123" in str(cookie_header)

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_streaming_chunks(
        self, backend: str, server: LocalTestServer, make_client
    ) -> None:
        """Both transports deliver chunks incrementally via stream_callback."""
        chunks = [b"chunk1-", b"chunk2-", b"chunk3"]
        server.add_route("GET", "/stream", chunked_response(chunks))

        received: list[bytes] = []
        client = await make_client(backend, verbose=False)
        await client.request(
            server.url("/stream"),
            return_type=ReturnType.STREAM,
            stream_callback=lambda chunk: received.append(chunk),
        )
        assert len(received) >= 1
        assert b"".join(received) == b"chunk1-chunk2-chunk3"

    @pytest.mark.parametrize("backend", _BACKENDS)
    async def test_backend_closes_cleanly(self, backend: str, server: LocalTestServer) -> None:
        """Both transports close without errors."""
        server.add_route("GET", "/ok", json_response({"ok": True}))
        client = FastRequests(backend=backend, verbose=False)
        async with client:
            await client.request(server.url("/ok"))
        # If we get here, close succeeded
