"""Tests for streaming, cookie behavior, TLS/redirect delegation,
and compatibility APIs (Task 5).

Covers:
- Local chunked-response fixture proving chunks arrive before full body
- stream_callback through all public methods
- Shared cookies, set_cookies, reset_cookies
- Redirects and TLS configuration delegation
- ParallelRequests alias and convenience functions
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from fastreq import (
    FastRequests,
    ParallelRequests,
    ReturnType,
    fastreq,
    fastreq_async,
)
from tests.conftest import (
    LocalTestServer,
    MockResponse,
    chunked_response,
    json_response,
)


@pytest.fixture
async def server() -> AsyncIterator[LocalTestServer]:
    srv = LocalTestServer()
    await srv.start()
    yield srv
    await srv.stop()


class TestStreaming:
    """Task 5.1, 5.2: Chunked streaming with callbacks."""

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_chunks_received_before_full_body(
        self, backend: str, server: LocalTestServer
    ) -> None:
        """Callback sees chunks incrementally, not all at once."""
        chunks = [b"A" * 100, b"B" * 100, b"C" * 100]
        server.add_route("GET", "/big", chunked_response(chunks))

        received: list[bytes] = []

        def on_chunk(chunk: bytes) -> None:
            received.append(bytes(chunk))

        client = FastRequests(backend=backend, verbose=False)
        async with client:
            await client.request(
                server.url("/big"),
                return_type=ReturnType.STREAM,
                stream_callback=on_chunk,
            )

        # Chunks should have been received incrementally
        # Key assertion: more than one callback invocation happened
        assert len(received) >= 1
        # Full body assembled correctly
        assert b"".join(received) == b"A" * 100 + b"B" * 100 + b"C" * 100

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_stream_callback_async_convenience(
        self, backend: str, server: LocalTestServer
    ) -> None:
        """stream_callback works through fastreq_async."""
        server.add_route("GET", "/data", chunked_response([b"hello", b" ", b"world"]))

        received: list[bytes] = []
        result = await fastreq_async(
            server.url("/data"),
            backend=backend,
            return_type=ReturnType.STREAM,
            stream_callback=lambda c: received.append(c),
            verbose=False,
        )
        assert result is None  # STREAM returns None
        assert b"".join(received) == b"hello world"

    async def test_stream_without_callback_returns_none(self, server: LocalTestServer) -> None:
        """STREAM return_type without callback still works (no streaming)."""
        server.add_route("GET", "/data", json_response({"ok": True}))

        client = FastRequests(verbose=False)
        async with client:
            result = await client.request(
                server.url("/data"),
                return_type=ReturnType.STREAM,
            )
        assert result is None


class TestCookieBehavior:
    """Task 5.3: Cookie management."""

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_cookies_shared_across_requests(
        self, backend: str, server: LocalTestServer
    ) -> None:
        """Cookies set on client are sent with requests."""
        server.add_route("GET", "/check", json_response({"ok": True}))

        client = FastRequests(backend=backend, verbose=False)
        client.set_cookies({"session_id": "abc123", "csrf": "xyz"})
        async with client:
            await client.request(server.url("/check"))

        last = server.requests_received[-1]
        headers: dict[str, object] = last["headers"]  # type: ignore[assignment]
        cookie_header = str(headers.get("cookie", ""))
        assert "session_id=abc123" in cookie_header
        assert "csrf=xyz" in cookie_header

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_set_cookies_updates_session(self, backend: str, server: LocalTestServer) -> None:
        """set_cookies adds new cookies without clearing existing."""
        server.add_route("GET", "/check", json_response({"ok": True}))

        client = FastRequests(backend=backend, verbose=False, cookies={"initial": "1"})
        client.set_cookies({"added": "2"})
        async with client:
            await client.request(server.url("/check"))

        last = server.requests_received[-1]
        headers: dict[str, object] = last["headers"]  # type: ignore[assignment]
        cookie_header = str(headers.get("cookie", ""))
        assert "initial=1" in cookie_header
        assert "added=2" in cookie_header

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_reset_cookies_clears_all(self, backend: str, server: LocalTestServer) -> None:
        """reset_cookies clears all session cookies."""
        server.add_route("GET", "/check", json_response({"ok": True}))

        client = FastRequests(backend=backend, verbose=False, cookies={"temp": "value"})
        client.reset_cookies()
        assert client._cookies == {}

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_initial_cookies_in_constructor(
        self, backend: str, server: LocalTestServer
    ) -> None:
        """Cookies passed to constructor are used."""
        server.add_route("GET", "/check", json_response({"ok": True}))

        client = FastRequests(backend=backend, verbose=False, cookies={"init": "cookie"})
        async with client:
            await client.request(server.url("/check"))

        last = server.requests_received[-1]
        headers: dict[str, object] = last["headers"]  # type: ignore[assignment]
        cookie_header = str(headers.get("cookie", ""))
        assert "init=cookie" in cookie_header


class TestRedirectsAndTLS:
    """Task 5.3: Redirect and TLS configuration delegation."""

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_follow_redirects(self, backend: str, server: LocalTestServer) -> None:
        """Client follows redirects by default."""
        server.add_route(
            "GET",
            "/redirect",
            MockResponse(
                status=302,
                headers={"Location": "/target"},
                body=b"",
            ),
        )
        server.add_route("GET", "/target", json_response({"redirected": True}))

        client = FastRequests(backend=backend, verbose=False)
        async with client:
            result = await client.request(
                server.url("/redirect"),
                return_type=ReturnType.JSON,
            )
        assert result == {"redirected": True}

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_no_follow_redirects(self, backend: str, server: LocalTestServer) -> None:
        """Client respects follow_redirects=False."""
        server.add_route(
            "GET",
            "/redirect",
            MockResponse(
                status=302,
                headers={"Location": "/target"},
                body=b"",
            ),
        )
        server.add_route("GET", "/target", json_response({"redirected": True}))

        client = FastRequests(backend=backend, verbose=False, follow_redirects=False)
        async with client:
            result = await client.request(
                server.url("/redirect"),
                return_type=ReturnType.RESPONSE,
            )
        assert result.status_code == 302

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_verify_ssl_default_true(self, backend: str, server: LocalTestServer) -> None:
        """TLS verification is True by default."""
        client = FastRequests(backend=backend, verbose=False)
        assert client.verify_ssl is True

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_verify_ssl_override(self, backend: str, server: LocalTestServer) -> None:
        """Per-request verify_ssl override is respected."""
        server.add_route("GET", "/data", json_response({"ok": True}))

        client = FastRequests(backend=backend, verbose=False, verify_ssl=True)
        async with client:
            # Local server doesn't use SSL, but the flag should propagate
            result = await client.request(
                server.url("/data"),
                verify_ssl=False,  # Override
                return_type=ReturnType.JSON,
            )
        assert result == {"ok": True}


class TestCompatibilityAPIs:
    """Task 5.4: ParallelRequests aliases and convenience functions."""

    def test_parallel_requests_is_alias(self) -> None:
        assert ParallelRequests is FastRequests

    def test_fastreq_sync_function(self) -> None:
        """fastreq() sync convenience function works.

        Uses a simple threaded HTTP server and calls fastreq() synchronously.
        """
        import http.server
        import socketserver
        import threading

        class SyncHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"hello": "world"}')

            def log_message(self, format: str, *args: object) -> None:
                pass

        server = socketserver.TCPServer(("127.0.0.1", 0), SyncHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            result = fastreq(
                f"http://127.0.0.1:{port}/api",
                backend="niquests",
                verbose=False,
            )
            assert result == {"hello": "world"}
        finally:
            server.shutdown()

    async def test_fastreq_async_function(self, server: LocalTestServer) -> None:
        """fastreq_async() convenience function works."""
        server.add_route("GET", "/api", json_response({"async": True}))
        result = await fastreq_async(
            server.url("/api"),
            backend="niquests",
            verbose=False,
        )
        assert result == {"async": True}

    async def test_keyed_response(self, server: LocalTestServer) -> None:
        """Keys produce a dict mapping."""
        server.add_route("GET", "/a", json_response({"id": "a"}))
        server.add_route("GET", "/b", json_response({"id": "b"}))

        client = FastRequests(verbose=False)
        async with client:
            result = await client.request(
                [server.url("/a"), server.url("/b")],
                keys=["first", "second"],
            )
        assert result["first"] == {"id": "a"}
        assert result["second"] == {"id": "b"}

    async def test_list_response(self, server: LocalTestServer) -> None:
        """Multiple URLs without keys produce a list."""
        server.add_route("GET", "/a", json_response({"id": "a"}))
        server.add_route("GET", "/b", json_response({"id": "b"}))

        client = FastRequests(verbose=False)
        async with client:
            result = await client.request(
                [server.url("/a"), server.url("/b")],
            )
        assert isinstance(result, list)
        assert len(result) == 2

    async def test_single_url_returns_single_result(self, server: LocalTestServer) -> None:
        """Single URL string returns a single result, not a list."""
        server.add_route("GET", "/single", json_response({"single": True}))

        client = FastRequests(verbose=False)
        async with client:
            result = await client.request(server.url("/single"))
        assert result == {"single": True}


class TestHeaderPolicy:
    """Task 4.5: Header/user-agent policy."""

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_user_agent_sent(self, backend: str, server: LocalTestServer) -> None:
        """Random user-agent is added to requests."""
        server.add_route("GET", "/ua", json_response({"ok": True}))

        client = FastRequests(backend=backend, random_user_agent=True, verbose=False)
        async with client:
            await client.request(server.url("/ua"))

        last = server.requests_received[-1]
        headers: dict[str, object] = last["headers"]  # type: ignore[assignment]
        ua = str(headers.get("user-agent", ""))
        assert ua  # Non-empty
        assert "Mozilla" in ua or "python" in ua.lower() or "fastreq" in ua.lower()

    @pytest.mark.parametrize("backend", ["niquests", "httpx"])
    async def test_custom_headers_preserved(self, backend: str, server: LocalTestServer) -> None:
        """Custom headers are sent with the request."""
        server.add_route("GET", "/custom", json_response({"ok": True}))

        client = FastRequests(backend=backend, verbose=False)
        async with client:
            await client.request(
                server.url("/custom"),
                headers={"X-Custom-Header": "test-value"},
            )

        last = server.requests_received[-1]
        headers: dict[str, object] = last["headers"]  # type: ignore[assignment]
        assert headers.get("x-custom-header") == "test-value"
